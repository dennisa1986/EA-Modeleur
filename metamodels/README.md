# metamodels/

Place XMI metamodel files here. These files are read by the `MetamodelCompiler` stage.

| File | Description |
|---|---|
| `ea17_base.xmi` | EA 17.1 base UML metamodel (to be exported from EA) |
| `uml24_profile.xmi` | UML 2.4 profile used for stereotype definitions |

## How to export from Enterprise Architect 17.1

1. Open the project in EA.
2. Go to **Publish → Technology → Publish as UML Profile…**
3. Select the package to export and save as `.xmi`.

The `MetamodelCompiler` expects XMI 2.1 format.
