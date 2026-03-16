# EA XMI Conventions

## Target version
Enterprise Architect 17.1, XMI 2.1 export format.

## Element GUIDs
EA requires every element to have a stable `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` GUID.
The pipeline assigns pipeline-internal UUIDs during ingestion; the serializer maps them to
EA-style GUIDs (with curly-brace wrapping) in the XMI output.

## Namespaces
Always declare these in the XMI root element:
```xml
xmlns:xmi="http://www.omg.org/XMI"
xmlns:uml="http://www.eclipse.org/uml2/5.0.0/UML"
xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
```

## Stereotype application
EA stereotypes are applied via `<xmi:Extension extender="Enterprise Architect">` blocks,
not via UML profile application.  The serializer must use this EA-specific pattern.

## Package hierarchy
EA models have a root package named `EA_Model`. All user packages nest inside it.
The `package_path` field in `CanonicalModel` uses dot-notation; the serializer converts
this to nested `packagedElement` tags.

## Diagrams
EA diagrams are serialized in the `<xmi:Extension>` block, not in the UML namespace.
Diagram layout (x/y positions) is out of scope for the initial implementation.

## Import format
The serializer targets EA's **XMI Import** (File → Import/Export → Import XMI).
Do not target the older `.eap` binary format.
