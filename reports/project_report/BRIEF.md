# Project report: brief for chapter drafts

Report: "RE-PEAT: peatland rewetting toolkit. Findings and proposed methodology", RE-PEAT GIS team, Departemen Teknik Geodesi UGM, October 2026. One Word file, English, assembled by `re-peat/tools/project_report.py` from the chapter files in `chapters/`.

## Audience

The World Bank and KLH (Kementerian Lingkungan Hidup). Technical readers who are not programmers. No code, file paths, command names, option names, function names or repository internals in the text. Name tools by what they do ("the DEM correction", "the interventions module"); the module names may appear once in chapter 2 only. The canal block and pumping module is called **RE-PEAT Interventions** (formerly repeat-pump). Numbers are required: every finding is stated with its number, unit, site and period.

The report is written by the RE-PEAT GIS team to its clients, in the voice of a methodology and findings report. Each section opens with what the finding means for rewetting decisions, then the method and evidence. Leave out what only matters to the team or its machines:

- local setup: the data folder, the data catalogue and its row counts, version control, scripts, Python, "on disk", "rerun", configuration files;
- internal working rules and agent instructions (data-only, no downscaling, reproducibility rules), internal decision IDs (D1-D21), dates of individual runs unless the date matters to the reader;
- run mechanics: steps that "stopped with an error", run times and read costs, tests "without a screen", which files a step reads;
- internal team discussion: "not yet agreed with the team", "the team has yet to confirm", who prefers what.

State a limitation by its effect on the result ("no water-table station lies inside Saleh-Sugihan, so no deficit can be computed"), not by what the software did.

## Rules

1. **Data only.** Every number, name and claim comes from a file in the workspace that you read in this task. Never type a number from memory. For each chapter, write a companion `chapters/<NN>_<slug>.sources.md`: one line per number or claim, giving the file (and line or column) it came from.
2. **References.** Cite as (Author Year) or (Author et al. Year). Cite only works that appear in the workspace reference lists or research notes (`repeat-neraca/docs/references.md`, `repeat-pump/docs/references.md`, `repeat-neraca/research_notes/`, `repeat-dem/docs/demnas-literature.md`, `re-peat/docs/`), and only for what that source says there. List every work you cite at the end of the sources file with the full reference and DOI or URL as given there. A separate check verifies each reference; unverified ones will be removed, so keep each claim's support clear.
3. **Status words.** Rankings use default weights proposed by the project for agreement with KLH and the World Bank, and adjustable in the dashboard: say so once per chapter where a ranking appears, in those terms (never "not yet agreed with the team"). The groundwater model is in development. Licence overlaps are worded as hotspots or burned area inside a licence area, never as responsibility; no company names. Skip the Banjarbaru (bandara) and other unofficial requests.
4. **Style.** Plain, specific prose; apply the humanizer skill (load it with the Skill tool, name `humanizer`) to your final text. No em or en dashes as punctuation (ranges like 0.4-0.6 m use a hyphen or "to"), no "not X but Y", no one-line closers, no bold labels on list items, no inflated words. Sentence-case headings. Short paragraphs; tables and figures carry the numbers where possible. British spelling (prioritisation, modelling).
5. **Code over docs.** Where a repository's docs differ from its code (defaults, thresholds, method steps, inputs), the code is right: describe what the code does and note the discrepancy in your sources file.
6. **Length.** Write what the evidence supports. Methodology is described fully enough that a reviewer could judge it; findings carry their numbers.

## Markdown format (the build script converts it)

- `#` is the chapter title (`# 4 DEM investigation`), `##` and `###` for sections. No deeper levels.
- Paragraphs, `-` bullet lists, `1.` numbered lists, `**bold**` and `*italic*` only.
- Tables: pipe tables, with a caption line directly above: `Table: <caption>. Source: <data source in words>.` Units in headers.
- Existing figure: `![<caption>. Source: ...>](<workspace-relative path to png>)` on its own line.
- Diagrams (method flows, workflows, decision trees) are draw.io files, so the team can edit and re-export them. Reuse an existing one where it fits (`repeat-neraca/docs/figures/neraca_method.drawio`, `repeat-pump/docs/figures/pump_method.drawio`, `re-peat/reports/dem_benchmark/dem_benchmark_workflow.drawio`) as `![caption](path.drawio)`; the build exports it to PNG. For a new diagram write `{{diagram: <id> | <caption> | <boxes and arrows it should show>}}`; it will be drawn in draw.io. Never draw a diagram with matplotlib.
- Figure to be generated: a line `{{figure: <id> | <caption> | <what it shows, chart type, the exact source file(s) and columns>}}`. Time series are lines. Maps: say the layer and the field. The build script will make it.
- Table to be generated from data: `{{table: <id> | <caption> | <exact source file(s), columns, rows>}}`.
- Indonesian working terms (KHG, sub-KHG, TMA, sekat kanal, neraca air, gambut) in italics on first use per chapter; the glossary is in the annex.

## Chapter 10: results per KHG (for the analyst of each KHG)

Chapter 10 has one section per KHG, in `chapters/khg/NN_<code>_<name>.md`, inserted by the line `{{include: khg}}` in `chapters/10_khg_results.md`. The maps and tables in each section are built from the KHG's own outputs in `_khg/<code>_<name>/`, so they appear by themselves once the chain has run for that KHG on its elevation models (`python re-peat/tools/khg_pipeline.py run --khg <code>`); until then the section shows "not yet available" notes.

To fill in your KHG:

1. Run the chain for your KHG on every elevation model that covers it.
2. Print the numbers behind your section: `python re-peat/tools/project_report_khg.py numbers <code>`.
3. Under each `<!-- Writing prompt: ... -->` comment in your file, write 2 to 4 sentences: what the figure or table shows for this KHG, how the elevation models differ, and why (canal density, LiDAR coverage, relief, land cover). Use only numbers from step 2 or from the chapters. Leave the prompts in place; the build skips them.
4. Add one line per number you quote to `chapters/khg/<same file name>.sources.md` (the build skips it).
5. Rebuild: `python re-peat/tools/project_report.py`, then `powershell -File re-peat/tools/docx_render.ps1 re-peat/reports/project_report/RE-PEAT_project_report.docx`.

`python re-peat/tools/project_report_khg.py init` creates a missing KHG file from the template; it never overwrites an existing one. Headings `## {n} ...` are numbered by the build.
