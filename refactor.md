# **Refactoring Paxman for Clean Architecture**

[https://gemini.google.com/app/06d155757f20f014](https://gemini.google.com/app/06d155757f20f014)

*User prompt: im planning to refactor my python canonicalization library, Paxman, so that every layer responsibility are cleanly cut, adhere to clean architecture and avoid maintenance nghtmare as the library rows bigger. The library function is to, giben an input, and contract(information category), able to recognize the information from the input and provide a canonical value in the format the user has selected (limited output format given). Paxman philosophy is it always cite the provenance, a reference of policy, standards, specifications, registries that are published by known authorities. So I have 3 layers of responsibiity. The Provenance layer maintain linkage of specs/policy/registries to an authority, and every rules in the specs/registries/policy are represented by either regex (for text mathcing), table (for lookup), parser (for value parsing). The Recognition layer is responisble to determine which provenence to use to recognize the value from a given text input. if any recognizable value is retrieved, it will record its provenance, and compile the result in list of RecognizedReps. RecognizedReps then goes through Resolver, to resolved the recognized value into validated values. Validated values then go through a cnicalizer to return the canonicalized values. If there are more than 1 canonical value, then the result is deemed ambigous. But my issue now, the resolver also has no idea its a valid value unless it referes to Provenance,*

Response: Your instinct here is spot on. Running into this wall is a classic sign that **Provenance** shouldn't just be treated as a passive metadata layer; it is actually the **Specification / Rule Engine** itself.

In Clean Architecture, when a downstream component (like the Resolver) needs access to upstream definitions (like rules, tables, or parsers) to do its job, it usually points to a conceptual flaw in how responsibilities are bounded. If the Resolver is blind without Provenance, it means **Provenance rules encapsulate both extraction *and* validation logic**.

To prevent Paxman from becoming a maintenance nightmare as it grows, we can refactor the architecture by shifting from rigid horizontal layers to a **Domain-Centric Pipeline** model where Rules are first-class domain objects that carry their own provenance, extraction, and validation logic.

### **Phase 1: Redefining the Core Concepts**

Instead of thinking in terms of separate layers (Provenance → Recognition → Resolver), structure Paxman around **Domain Specifications** and **Stateless Engines**.

> 1. **The Specification (The Rule Unit):** A "Specification" (or Rule) is a unified domain entity. It contains:  
   * **Provenance Metadata:** Authority, specification name, version, official URL.  
   * **Extraction Logic:** How to find it (the Regex, Table lookup, or Parser).  
   * **Validation / Resolution Logic:** How to check if the extracted raw match is valid and how to normalize it into a canonical form.  
> 2. **The Recognition Engine:** Purely responsible for scanning text against a selected contract's rules and extracting raw matches, outputting a RecognizedRep that securely bundles the raw string *and* a reference to the rule that caught it.  
> 3. **The Resolution Engine:** Takes the RecognizedRep, inspects it, and invokes the rule's built-in validation/normalization logic to produce a ValidatedRep or canonical value.

### **Phase 2: Restructuring the Architecture**

Here is how you can cleanly separate responsibilities to respect Clean Architecture boundaries:

`[ Contracts & Configuration ] (Outer / Application Edge)`  
           `│`  
           `▼`  
`[ Pipeline Orchestrator ]     (Use Case Layer)`  
   `├──> Recognition Engine    (Domain Service)`  
   `└──> Resolution Engine     (Domain Service)`  
           `│`  
           `▼`  
`[ Specifications / Rules ]    (Enterprise Business Rules / Core Domain)`  
   `├──> Authority & Provenance`  
   `├──> Matchers (Regex/Table/Parser)`  
   `└──> Validators / Normalizers`

#### **1\. The Core Domain (paxman.domain)**

> * **Specification (Abstract Base or Protocol):** Every rule implements this. It encapsulates the provenance and the behavior.  
>   `class Specification:`  
>       `authority: Authority`  
>       `version: str`  
>       `provenance_url: str`

>       `def extract(self, text: str) -> list[RawMatch]: ...`  
>       `def validate_and_resolve(self, raw_match: RawMatch) -> CanonicalValue: ...`

> * **Concrete Rules (RegexSpecification, TableSpecification, ParserSpecification):** Implement the specific matching and validation mechanisms. Because validation lives *inside* the rule definition, the Resolver doesn't need to "know" about Provenance—it just asks the rule bound to the RecognizedRep to validate itself.

#### **2\. The Engines (paxman.engines)**

> * **Recognition Engine:** Takes a contract, fetches the relevant active specifications, and runs them. It outputs RecognizedRep objects. Crucially, a RecognizedRep should hold a direct reference (or identifier) to the Specification that produced it.  
> * **Resolver Engine:** Takes the RecognizedRep, looks at the attached specification reference, and calls spec.validate\_and\_resolve(rep). This eliminates the coupling issue: the Resolver doesn't query a global provenance database; it simply delegates validation back to the rule object that already understands the domain constraint.

### **Phase 3: Handling the Ambiguity Check**

Since your requirement states that *more than 1 canonical value yields an ambiguous result*, your Pipeline Orchestrator can handle this cleanly at the final stage:

> 1. **Recognition Phase:** Yields multiple RecognizedRep instances from various rules/provenances.  
> 2. **Resolution Phase:** Each RecognizedRep is passed to its respective specification's validation logic, resulting in a list of candidate CanonicalValue objects (each strictly carrying its provenance trail).  
> 3. **Ambiguity & Selection Phase:**  
   * If len(canonical\_values) \== 0: Return un-routable / not found.  
   * If len(canonical\_values) \== 1: Return the single canonical value with full provenance.  
   * If len(canonical\_values) \> 1: Flag as **Ambiguous**, returning all conflicting canonical values alongside their respective provenances so the user can see *why* it conflicted.

To help tailor the next step of this refactor, **how are your contracts currently structured—are they declarative config files (like YAML/JSON) that map to python rule classes, or are they entirely code-defined?**

---

*User prompt: They are code defined, user calls paxman.canonicalize("azahari at gmail dot com", Email(include\_obsfuscated=true))*

Response: That code-defined style (paxman.canonicalize(..., Email(include\_obsfuscated=True))) actually makes your Clean Architecture design **much cleaner**.

When contracts are code-defined objects, the contract itself becomes the configuration factory. It decides *which* rules (and by extension, which provenances) are active for that specific execution context.

Because the validation logic and provenance belong to the same rule, your **Resolver no longer needs to query an external provenance registry**. It simply asks the matched rule to validate and normalize the raw input.

### **The Clean Architecture Blueprint for Paxman**

Here is how you can structure this cleanly using code-defined contracts:

#### **1\. The Rule / Specification (Core Domain)**

Every rule is a self-contained unit that bundles its **Provenance**, its **Matcher** (Regex/Table/Parser), and its **Validator/Normalizer**.

`from dataclasses import dataclass`  
`from typing import Protocol, Optional`

`@dataclass(frozen=True)`  
`class Provenance:`  
    `authority: str`  
    `specification_name: str`  
    `reference_url: str`

`class Rule(Protocol):`  
    `provenance: Provenance`  
      
    `def match(self, text: str) -> list[str]:`  
        `"""Extracts raw string matches from text."""`  
        `...`  
          
    `def validate_and_normalize(self, raw_value: str) -> Optional[str]:`  
        `"""Validates the raw match and returns the canonicalized form, or None if invalid."""`  
        `...`

#### **2\. Concrete Rules (Implementing the Contract)**

For example, an obfuscated email rule knows how to parse text like "azahari at gmail dot com" and validate it using its specific policy reference.

`class ObfuscatedEmailRule:`  
    `provenance = Provenance(`  
        `authority="IETF / Community Standard",`  
        `specification_name="RFC 5322 (Obfuscated Notation)",`  
        `reference_url="https://tools.ietf.org/html/rfc5322"`  
    `)`  
      
    `def match(self, text: str) -> list[str]:`  
        `# Regex or parser logic to find "X at Y dot Z"`  
        `...`  
        `return ["azahari at gmail dot com"]`

    `def validate_and_normalize(self, raw_value: str) -> Optional[str]:`  
        `# Translates "at" -> "@", "dot" -> ".", validates structural integrity`  
        `cleaned = raw_value.replace(" at ", "@").replace(" dot ", ".")`  
        `if "@" in cleaned and "." in cleaned:`  
            `return cleaned.lower()`  
        `return None`

#### **3\. The Contract Object (Application Edge)**

The user passes an instance of a contract, which dynamically configures which rules are brought into play.

`class Email:`  
    `def __init__(self, include_obsfuscated: bool = False):`  
        `self._rules: list[Rule] = [StandardEmailRule()]`  
        `if include_obsfuscated:`  
            `self._rules.append(ObfuscatedEmailRule())`  
              
    `@property`  
    `def rules(self) -> list[Rule]:`  
        `return self._rules`

#### **4\. The Pipeline / Orchestrator (Use Case Layer)**

The orchestrator coordinates the execution without needing to know the inner workings of regex or validation rules. It delegates everything to the rules provided by the contract.

`@dataclass`  
`case class RecognizedRep:`  
    `raw_value: str`  
    `rule: Rule`

`@dataclass`  
`case class CanonicalResult:`  
    `value: str`  
    `provenance: Provenance`

`class CanonicalizationPipeline:`  
    `def execute(self, text: str, contract: Email) -> CanonicalResult:`  
        `recognized_reps = []`  
          
        `# 1. Recognition Phase`  
        `for rule in contract.rules:`  
            `raw_matches = rule.match(text)`  
            `for raw in raw_matches:`  
                `recognized_reps.append(RecognizedRep(raw_value=raw, rule=rule))`  
                  
        `# 2. Resolution & Validation Phase`  
        `resolved_results = []`  
        `for rep in recognized_reps:`  
            `canonical_val = rep.rule.validate_and_normalize(rep.raw_value)`  
            `if canonical_val is not None:`  
                `resolved_results.append(`  
                    `CanonicalResult(value=canonical_val, provenance=rep.rule.provenance)`  
                `)`  
                  
        `# 3. Ambiguity Check`  
        `unique_values = {res.value for res in resolved_results}`  
          
        `if len(unique_values) == 0:`  
            `raise ValueError("No recognizable valid value found.")`  
        `if len(unique_values) > 1:`  
            `raise AmbiguousResultError(resolved_results) # More than 1 distinct canonical value!`  
              
        `return resolved_results[0]`

### **Why This Fixes Your Issue**

> 1. **Decoupling Solved:** The Resolver doesn't need to look up Provenance to know if a value is valid because the validation logic lives **inside** the rule object that already possesses the Provenance.  
> 2. **Clean Architecture Compliance:**  
   * **Domain Core:** Rules, Provenance, and Validation logic.  
   * **Application/Contracts:** Email(...) objects acting as use-case configurations.  
   * **Orchestrator:** Pure pipeline logic moving data from Text → Matches → Validated Canonical Values.  
> 3. **Seamless Extensibility:** When you want to add a new category or rule later, you just create a new Rule class with its own Provenance and validation methods, and plug it into the contract.

---

*User prompt: my rule is right now validating email as 2 parts validation. local\_part and domain\_part. And other than obfuscated email rule, i also have localhost email rule and standard email rule. and i want the input to go throu all registered rules so that it exhaustively recognized the value and create all the RecognizedReps*

Response: Exhaustive recognition is the gold standard for a provenance-first library like Paxman. By running the input through *all* registered rules instead of short-circuiting on the first match, you surface every possible interpretation. This is crucial for catching ambiguities (e.g., whether an input is an intentional obfuscation or a malformed standard address).

Since your email validation relies on checking a **local part** and a **domain part**, you can easily solve code duplication by extracting the structural email validation into a **shared domain helper or base class**, while letting each rule handle its unique matching and text preprocessing.

### **Step 1: Create a Shared Email Validator (Base Class or Utility)**

Instead of rewriting local and domain part validation for every rule, encapsulate it in a shared base or validator component.

`import re`  
`from typing import Optional, List`  
`from dataclasses import dataclass`

`@dataclass(frozen=True)`  
`class Provenance:`  
    `authority: str`  
    `specification_name: str`  
    `reference_url: str`

`class BaseEmailRule:`  
    `"""Shared logic for validating local and domain parts according to specs."""`  
      
    `def _validate_parts(self, local_part: str, domain_part: str) -> bool:`  
        `# Common local part checks (e.g., length, allowed chars)`  
        `if not local_part or len(local_part) > 64:`  
            `return False`  
        `# Common domain part checks`  
        `if not domain_part or len(domain_part) > 255:`  
            `return False`  
        `return True`

### **Step 2: Implement Specialized Rules**

Each rule inherits the shared validation logic or uses it, but implements its own **matcher** (how it finds the text) and **normalizer** (how it prepares the raw match before validation).

`class StandardEmailRule(BaseEmailRule):`  
    `provenance = Provenance(`  
        `authority="IETF",`  
        `specification_name="RFC 5322 (Standard Internet Email)",`  
        `reference_url="https://tools.ietf.org/html/rfc5322"`  
    `)`  
      
    `def match(self, text: str) -> List[str]:`  
        `# Standard regex for user@domain.tld`  
        `pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"`  
        `return re.findall(pattern, text)`

    `def validate_and_normalize(self, raw_value: str) -> Optional[str]:`  
        `parts = raw_value.split("@")`  
        `if len(parts) != 2:`  
            `return None`  
        `local, domain = parts`  
          
        `if self._validate_parts(local, domain):`  
            `return f"{local.lower()}@{domain.lower()}"`  
        `return None`

`class ObfuscatedEmailRule(BaseEmailRule):`  
    `provenance = Provenance(`  
        `authority="Community Anti-Spam Standard",`  
        `specification_name="RFC 5322 (Obfuscated Notation / Human-Readable)",`  
        `reference_url="https://datatracker.ietf.org/doc/html/rfc5322"`  
    `)`  
      
    `def match(self, text: str) -> List[str]:`  
        `# Matches patterns like "user at domain dot com"`  
        `pattern = r"\b[A-Za-z0-9._%+-]+\s+(?:at|@)\s+[A-Za-z0-9.-]+\s+dot\s+[A-Za-z]{2,}\b"`  
        `return re.findall(pattern, text, re.IGNORECASE)`

    `def validate_and_normalize(self, raw_value: str) -> Optional[str]:`  
        `# Preprocess obfuscation into standard structure`  
        `normalized_raw = raw_value.lower()`  
        `normalized_raw = re.sub(r"\s+(?:at|@)\s+", "@", normalized_raw)`  
        `normalized_raw = re.sub(r"\s+dot\s+", ".", normalized_raw)`  
          
        `parts = normalized_raw.split("@")`  
        `if len(parts) != 2:`  
            `return None`  
        `local, domain = parts`  
          
        `if self._validate_parts(local, domain):`  
            `return f"{local}@{domain}"`  
        `return None`

`class LocalhostEmailRule(BaseEmailRule):`  
    `provenance = Provenance(`  
        `authority="IETF",`  
        `specification_name="RFC 6761 (Special-Use Domain Names - Localhost)",`  
        `reference_url="https://tools.ietf.org/html/rfc6761"`  
    `)`  
      
    `def match(self, text: str) -> List[str]:`  
        `pattern = r"\b[A-Za-z0-9._%+-]+@(?:localhost|.+\.local)\b"`  
        `return re.findall(pattern, text, re.IGNORECASE)`

    `def validate_and_normalize(self, raw_value: str) -> Optional[str]:`  
        `parts = raw_value.split("@")`  
        `if len(parts) != 2:`  
            `return None`  
        `local, domain = parts`  
          
        `# Localhost rules permit '.local' or 'localhost' as domains`  
        `if domain.lower() in ["localhost", "local"] or domain.endswith(".local"):`  
            `if self._validate_parts(local, domain):`  
                `return f"{local.lower()}@{domain.lower()}"`  
        `return None`

### **Step 3: Exhaustive Recognition Orchestrator**

To ensure *all* rules are evaluated and every potential match is extracted, the orchestrator iterates completely through the rule list without stopping early:

`@dataclass`  
`class RecognizedRep:`  
    `raw_value: str`  
    `rule: any`

`@dataclass`  
`class CanonicalResult:`  
    `value: str`  
    `provenance: Provenance`

`class CanonicalizationPipeline:`  
    `def execute(self, text: str, contract) -> List[CanonicalResult]:`  
        `recognized_reps: List[RecognizedRep] = []`  
          
        `# 1. Exhaustive Recognition Phase`  
        `for rule in contract.rules:`  
            `raw_matches = rule.match(text)`  
            `for raw in raw_matches:`  
                `recognized_reps.append(RecognizedRep(raw_value=raw, rule=rule))`  
                  
        `# 2. Resolution & Validation Phase`  
        `resolved_results: List[CanonicalResult] = []`  
        `for rep in recognized_reps:`  
            `canonical_val = rep.rule.validate_and_normalize(rep.raw_value)`  
            `if canonical_val is not None:`  
                `resolved_results.append(`  
                    `CanonicalResult(value=canonical_val, provenance=rep.rule.provenance)`  
                `)`  
                  
        `# 3. Deduplication & Ambiguity Handling`  
        `# Group by canonical value to detect true conflicts vs redundant identical matches`  
        `unique_canonical_map = {res.value: res for res in resolved_results}`  
          
        `if len(unique_canonical_map) == 0:`  
            `raise ValueError("No recognizable valid value found.")`  
          
        `if len(unique_canonical_map) > 1:`  
            `# Ambiguity detected: Multiple different valid canonical values matched!`  
            `raise AmbiguousResultError(list(unique_canonical_map.values()))`  
              
        `return list(unique_canonical_map.values())[0]`

### **Why This Design Scales**

> * **Zero Boilerplate Validation:** BaseEmailRule handles structural validation of local\_part and domain\_part once.  
> * **Exhaustive Extraction:** Input text is scanned by StandardEmailRule, ObfuscatedEmailRule, and LocalhostEmailRule independently. If an input matches multiple rules, both are recorded as RecognizedRep instances.  
> * **Built-in Provenance Traceability:** Even when multiple rules evaluate the input, every resulting canonical value permanently maintains its strict link back to its originating authority and specification standard.

---

*User prompt: so provenance only comes into play once in pipeline rule which is the concrete implementation of the base email rule. and each RecognizedReps will carry its own Prevenence*

Response: Spot on. You have nailed the exact mechanism.

By decentralizing provenance into each **concrete rule class**, you eliminate the need for a separate global provenance registry or database lookup during runtime.

Here is how that relationship looks in practice:

> 1. **The Rule Owns Its Provenance:** Every concrete rule class (StandardEmailRule, ObfuscatedEmailRule, etc.) statically declares its own Provenance metadata because it represents a specific standard or policy.  
> 2. **The RecognizedRep Inherits It:** When a rule extracts a raw match from the text, it wraps that match into a RecognizedRep that holds a reference back to the rule (or directly to the rule's Provenance).  
> 3. **Zero Lookups Required:** Down in the resolution and validation phases, the pipeline doesn't need to ask an external service what standard a value belongs to—the provenance is already riding along with the recognized representation.

This keeps your Clean Architecture strictly bounded:

> * **Core Domain:** Concrete rules encapsulate the matching logic, validation, *and* their own official authorities.  
> * **Orchestrator / Pipeline:** Simply sweeps through the rules, collects the RecognizedRep objects, and lets each rule validate itself while preserving its exact provenance trail.

---

*User prompt: i think i want to seperate my recognition layer out. Because recognization does not need to comform to certain standards/specifications. Recognition rules are written by contributors and the more Recognition rules there are the smarteer the library gets. But all recognition rule maker must understood that any recognized value must be transformed into recognized notation for example, under Email capability (paxman comes with multiple capabilities). Its recognized email notation is \[local-part, domain-part\] There are a few recognition rules. StandardRecognition recognize "email:azahari@gmail.com", "azahari@nexusnv.net" and produced \["azahari","@gmail.com"\] and \["azahari","@nexusnv.net"\] respectively. StandardRecognition cannot recognized "azahari at nexusnv dot net", that input requires ObfuscatedEmailRecognition that will match the regex and return \["azahari", "@nexusnv.net"\], and input "azahari at gmail dot co.m" into \["azahari","@gmail.co.m"\]. These are called RecognizedRep and single input may have multiple Reps. The next part is where provenance will play role. the Validation layer. This is the part Paxman never claims any value is valid, only a backed citation of specifications/reference/registries or policy is consider valid. ValidationRules ties provenace to the input. all Validation rules must have provenance. Email validation accepts \[local-part,domain-part\], In another capability, date validation accepts three-parts-bracket date notation eg: \["juli","12","26"\], \["Julai","1",2000"\], \["2026","1","2"\]. and this now creates another confusion. shold recognition take that extra steps to normalized juli and Julai into \[7\] or that is the responsibility of the Validation layer? and Does both Recognition layer and Validation layer must have awarenoess of the contract? becuase my contract for date has few argumants Date(two\_digit\_base\_year=2000, output\_format=ISO)*

Response: Separating the **Recognition layer** from the **Validation layer** is a brilliant architectural move. It creates a powerful ecosystem: anyone can write a clever regex or parser to recognize a messy string and turn it into a standard intermediate notation, while the heavy, trusted lifting of deciding if that notation is *actually valid* remains tied strictly to official specifications and Provenance.

Let’s break down your two critical questions regarding this clean separation: **Normalization boundaries** and **Contract awareness**.

### **Part 1: Where Does Normalization Happen ("Julai" → 7)?**

To keep the layers cleanly cut, use this golden rule: **Recognition handles syntax; Validation/Provenance handles semantics.**

> * **The Recognition Layer's Job:** Purely syntactic extraction. It scans the raw text and chops it into the agreed capability notation.  
  * *Example for Date:* A recognition rule extracts tokens as they appear in the text: \["Julai", "1", "2000"\] or \["26", "12", "07"\].  
  * Contributor-written recognizers don't need to worry about official calendars, leap years, or language registries. Their only job is: *"I found these three chunks of text that look like a date; here is the intermediate array."*  
> * **The Validation / Provenance Layer's Job:** Semantic translation and rule enforcement.  
  * When the RecognizedRep (\["Julai", "1", "2000"\]) hits a Validation Rule backed by a specification (e.g., *ISO 8601 / Malay Locale Registry*), the validator says: *"Ah, 'Julai' matches the Malay month registry for month 7\. Let's normalize this into semantic components: \[7, 1, 2000\]."*

**Why this matters:** If a contributor had to normalize "Julai" to 7, they would have to hardcode localization dictionaries inside the recognition rule. By pushing semantic mapping into Validation, recognition stays lightweight and hyper-focused on pattern matching.

### **Part 2: Does Both Layers Need Awareness of the Contract?**

Yes, but in **fundamentally different ways**.

Your user code looks like this: paxman.canonicalize(text, Date(two\_digit\_base\_year=2000, output\_format=ISO))

Here is how the Contract interacts with both layers:

#### **1\. Contract & the Recognition Layer (Filtering & Activation)**

The Recognition layer needs to know **what kind of recognizers are allowed to run** based on the contract configuration.

> * *Example:* If a user passes a contract configuration that disallows two-digit years (e.g., allow\_two\_digit\_years=False), the Recognition selector uses this to **filter out** the TwoDigitDateRecognition rule so it doesn't waste CPU cycles extracting ambiguous dates.  
> * *Implementation:* The contract acts as a factory or filter that passes a set of active recognizers to the Recognition engine.

#### **2\. Contract & the Validation/Canonicalization Layer (Execution Parameters)**

The Validation and Canonicalization layers need the contract parameters to **perform their logic and format the output**.

> * *Example:* The two\_digit\_base\_year=2000 argument isn't needed by the regex matcher. It is desperately needed by the Validator when it encounters \["26", "12", "07"\] so it can calculate that "26" means 2026\.  
> * *Example:* The output\_format=ISO argument is handed to the final Canonicalizer to dictate whether the validated data becomes YYYY-MM-DD or another supported structure.

### **The Clean Architecture Pipeline Flow**

Your updated flow becomes a crisp, multi-stage assembly line:

`[ Raw Input Text ]`  
       `│`  
       `▼`  
`[ Recognition Layer ] (Contributor-friendly)`  
   `* Scans text using active recognition rules (filtered by Contract).`  
   `* Extracts raw syntax into Capability Notations.`  
   `* Outputs: List[RecognizedRep] containing intermediate arrays (e.g., ["Julai", "1", "2000"]).`  
       `│`  
       `▼`  
`[ Validation & Provenance Layer ] (Standards-bound)`  
   `* Applies rules backed by official specs/registries.`  
   `* Uses Contract parameters (e.g., two_digit_base_year) to resolve semantics.`  
   `* Normalizes syntax into validated components and attaches Provenance.`  
   `* Outputs: List[ValidatedRep] with full citations.`  
       `│`  
       `▼`  
`[ Resolver & Ambiguity Check ]`  
   `* Checks if multiple distinct valid values exist.`   
   `* Triggers Ambiguity exception if > 1.`  
       `│`  
       `▼`  
`[ Canonicalizer Layer ]`  
   `* Formats the single validated value into the user's requested output_format (e.g., ISO).`

### **Summary of Responsibilities**

| Layer | Responsibility | Example | Contract Involvement |
| :---- | :---- | :---- | :---- |
| **Recognition** | Syntax extraction & tokenization. | "juli 12 26" → \["juli", "12", "26"\] | Used to enable/disable specific recognizer classes. |
| **Validation / Provenance** | Semantic checks, localization lookup, and standard citation. | Translating "juli" → 7, applying base year 2000\. | Uses parameters like two\_digit\_base\_year to execute rules. |
| **Canonicalizer** | Output formatting. | \[7, 12, 2026\] → "2026-07-12" | Uses output\_format=ISO to format the final result. |

---

*User prompt: that is a great solution. now the last part is the output shape. the current output shape i have is pasted below and i thin this is not the shape i want and its confusing. The candidate is blank, i want it to have all the candidates. in case of succuss outcome, only one candidate is present and if ambigous, there are 2 or more candidates. The evidence and authority is also looks like out of place {   "status": "CANONICALIZED",   "input\_value": "azahari at gmail dot com",   "canonicalized\_value": "azahari@gmail.com",   "evidence": \[     {       "rule": "deobfuscated\_verbal\_at\_dot",       "detail": "",       "authority": {         "name": "RFC 5322 \+ paxman spec/email",         "edition": "RFC 5322 §3.4.1 (addr-spec) \+ paxman spec/email §2.4 (recognition grammar)",         "kind": "grammar",         "version": "RFC 5322 §3.4.1 (addr-spec) \+ paxman spec/email §2.4 (recognition grammar)",         "publisher": null,         "released\_on": null,         "lifecycle": "active",         "checksum": null,         "retrieved\_at": null,         "supports\_multiple\_editions": false       }     }   \],   "candidates": null,   "contract": {     "kind": "canonical\_email",     "lowercase": true,     "strip\_whitespace": true,     "provider\_aliases": "gmail",     "strict": false,     "output\_format": "email",     "version": 1,     "include\_grammar": \[\],     "exclude\_grammar": \[\]   },   "version\_stamp": {     "paxman\_version": "0.0.0.dev0",     "contract\_version": 1,     "capabilities\_hash": "974e739bbb8211219d3a64859a6d6270a6b22cb0809fb4df022cc637cac6ef1b",     "configuration\_version": "0"   },   "authorities": \[     {       "name": "RFC 5322 \+ paxman spec/email",       "edition": "RFC 5322 §3.4.1 (addr-spec) \+ paxman spec/email §2.4 (recognition grammar)",       "kind": "grammar",       "version": "RFC 5322 §3.4.1 (addr-spec) \+ paxman spec/email §2.4 (recognition grammar)",       "publisher": null,       "released\_on": null,       "lifecycle": "active",       "checksum": null,       "retrieved\_at": null,       "supports\_multiple\_editions": false     }   \] }*

Response: Your critique hits the nail on the head. Having evidence, authorities, and candidates float around at the root level is structurally broken—especially for a library like Paxman.

If you have multiple competing candidates (ambiguity), **different candidates might be backed by different authorities or rules**. Lumping authorities into a single global root array makes it impossible to tell which authority backs which candidate.

To fix this, **Provenance and Authority must belong to the Candidate itself**.

### **The Redesigned JSON Output Structure**

Here is a clean, intuitive output shape where **candidates is always populated**, authorities/evidence are scoped per candidate, and the root state dynamically reflects whether the result is success or ambiguity.

#### **Scenario A: Successful Canonicalization (1 Candidate)**

`{`  
  `"status": "CANONICALIZED",`  
  `"input_value": "azahari at gmail dot com",`  
  `"canonicalized_value": "azahari@gmail.com",`  
  `"candidates": [`  
    `{`  
      `"value": "azahari@gmail.com",`  
      `"recognition_rule": "deobfuscated_verbal_at_dot",`  
      `"validation_rule": "rfc_5322_email_validator",`  
      `"provenance": {`  
        `"authority": "IETF",`  
        `"specification_name": "RFC 5322 §3.4.1 (addr-spec)",`  
        `"kind": "grammar",`  
        `"lifecycle": "active",`  
        `"reference_url": "https://tools.ietf.org/html/rfc5322"`  
      `}`  
    `}`  
  `],`  
  `"contract": {`  
    `"kind": "canonical_email",`  
    `"lowercase": true,`  
    `"strip_whitespace": true,`  
    `"output_format": "email",`  
    `"version": 1`  
  `},`  
  `"version_stamp": {`  
    `"paxman_version": "0.0.0.dev0",`  
    `"contract_version": 1,`  
    `"capabilities_hash": "974e739bbb8211219d3a64859a6d6270a6b22cb0809fb4df022cc637cac6ef1b"`  
  `}`  
`}`

#### **Scenario B: Ambiguous Result (2+ Candidates)**

When the pipeline finds multiple distinct valid canonical values, canonicalized\_value safely drops to null, status changes to AMBIGUOUS, and **all competing candidates—along with their distinct provenances—are listed side-by-side**.

`{`  
  `"status": "AMBIGUOUS",`  
  `"input_value": "some ambiguous text input",`  
  `"canonicalized_value": null,`  
  `"candidates": [`  
    `{`  
      `"value": "result_alpha@domain.com",`  
      `"recognition_rule": "recognition_rule_v1",`  
      `"validation_rule": "standard_policy_validator",`  
      `"provenance": {`  
        `"authority": "Authority A",`  
        `"specification_name": "Spec A Rule 1",`  
        `"kind": "policy",`  
        `"lifecycle": "active",`  
        `"reference_url": "https://example.com/spec-a"`  
      `}`  
    `},`  
    `{`  
      `"value": "result_beta@domain.com",`  
      `"recognition_rule": "recognition_rule_v2",`  
      `"validation_rule": "lax_policy_validator",`  
      `"provenance": {`  
        `"authority": "Authority B",`  
        `"specification_name": "Spec B Registry 4",`  
        `"kind": "registry",`  
        `"lifecycle": "active",`  
        `"reference_url": "https://example.com/spec-b"`  
      `}`  
    `}`  
  `],`  
  `"contract": {`  
    `"kind": "canonical_email",`  
    `"version": 1`  
  `},`  
  `"version_stamp": {`  
    `"paxman_version": "0.0.0.dev0",`  
    `"contract_version": 1`  
  `}`  
`}`

### **Why This Fixes the Confusion**

> 1. **Self-Contained Candidates:** Every item in the candidates array is a fully independent record. It tells the user: *"Here is the value we got, which recognition rule caught it, which validation rule approved it, and the exact authority/provenance backing it."*  
> 2. **No More Root-Level Clutter:** Root-level evidence and authorities arrays are completely removed because they are logically meaningless at a global level when multiple rules are involved.  
> 3. **Predictable State Handling:**  
   * status: "CANONICALIZED" → canonicalized\_value is populated, candidates has exactly 1 entry.  
   * status: "AMBIGUOUS" → canonicalized\_value is null, candidates has 2+ entries showing the conflict.  
   * status: "NOT\_FOUND" → canonicalized\_value is null, candidates is empty (\[\]).

---

