---
id: kno-01m2emy5vrfe
title: Render ticket bodies and notes as markdown
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:41.400393Z'
updated: '2026-09-14T00:37:42.281923Z'
closed: '2026-09-14T00:31:15.884027Z'
assignee: Jason Risch
---

## Description
A ticket's sections and notes are knot's markdown, and the ticket page shows them as raw text: the bold timestamps knot writes above each note come out as literal asterisks, bullet lists as dashes, code spans as backticks. Seen on the outcry backlog, where the epics carry paragraphs of design text and six or seven notes each. The page is where a reader should be able to read a ticket, and today it is not.

## Design
Render each section and each note through a markdown library with HTML escaping on, so a ticket body cannot inject markup; keep Jinja's autoescape and mark only the renderer's output safe. Headings inside a section render one level below the section's own. Assert on the page that a list, a code span and a bold run render as elements, and that a script tag in a ticket body renders as text.

## Notes

**2026-09-14T00:31:14.542930Z**

Task completed: sections and notes render through markdown-it-py in CommonMark mode with raw HTML off, so a tag in a ticket body is shown as text; a body's own headings are pushed two levels below the section heading; the templates apply a prose filter and the stylesheet gives lists, code and headings modest spacing. Asserted for lists, code, emphasis, a script tag, heading levels, and on the page.

**2026-09-14T00:35:04.082923Z**

Task completed: sections and notes render through markdown-it-py in CommonMark mode with raw HTML off, so a tag in a ticket body is shown as text; a body's own headings are pushed two levels below the section heading; the templates apply a prose filter and the stylesheet gives lists, code and headings modest spacing. The one Markup call is annotated for semgrep with the reason the audit rule asks for. Asserted for lists, code, emphasis, a script tag, heading levels, and on the page.

**2026-09-14T00:37:42.281923Z**

(see earlier note)
