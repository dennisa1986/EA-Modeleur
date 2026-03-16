# Skill: compile-metamodel

## Purpose
Compile an XMI metamodel file into a `RuleSet` JSON and print or save it.

## Usage
```
/compile-metamodel <path-to.xmi> [--output <ruleset.json>]
```

## Steps
1. Locate the XMI file (relative to `metamodels/` if not an absolute path).
2. Run `MetamodelCompiler.compile()`.
3. Serialise the `RuleSet` to JSON.
4. Print to stdout or write to `--output` if specified.
