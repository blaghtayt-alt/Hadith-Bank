#!/usr/bin/env python3
"""Chromium DOM parity for the lossless generated static-page optimizations.

Exercises synthetic source/provenance panels before/after and source-bound site
pages with JavaScript disabled. Never modifies source files or staged pages.
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

from build_discovery import (compact_static_record_markup,
                             compact_source_definition_end_tags,
                             compact_static_page_shell)


def require(value, message):
    if not value:
        raise ValueError('Static DOM browser check: ' + message)


def snapshot(page, markup):
    page.set_content(markup)
    return page.evaluate("""() => {
      const scope=document.querySelector('#fixture');
      return {dom:scope?.outerHTML, text:scope?.textContent,
        links:[...scope.querySelectorAll('a')].map(a=>[a.getAttribute('href'),a.getAttribute('target')]),
        roles:[...scope.querySelectorAll('[lang],[dir]')].map(a=>
          [a.tagName,a.getAttribute('lang'),a.getAttribute('dir')]),
        definitions:[...scope.querySelectorAll('dt,dd')].map(a=>[a.tagName,a.textContent])};
    }""")


def run(site_root):
    site_root = Path(site_root).resolve()
    paths = sorted((site_root / 'hadith').glob('**/*.html'))
    require(paths, 'no staged static narration pages')
    example = ('<section id="fixture"><h1>TEST مصدر 日本語</h1>'
               '<dl><dt>Source edition</dt><dd dir="auto"><a href="../../source/?x=1&amp;y=2">'
               'TEST Verified source</a></dd><dt>Translation origin</dt>'
               '<dd dir="auto">Human ≠ Unknown</dd></dl>'
               '<details class="language-reading" open><summary>TEST Arabic reading</summary>'
               '<div class="quotation" lang="ar" dir="rtl">نص تجريبي محفوظ، لا يُغيّر</div>'
               '</details></section>')
    compact = compact_source_definition_end_tags(compact_static_record_markup(example))
    require(len(compact.encode('utf-8')) < len(example.encode('utf-8')),
            'optional-tag fixture did not save bytes')
    document = ('<!doctype html>\n<html lang="fa"><head><title>TEST original</title>'
                '<script type="application/ld+json">{"@type":"CreativeWork","name":"TEST"}</script>'
                '</head><body>' + compact + '</body></html>')
    compact_document = compact_static_page_shell(document)
    checked = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(java_script_enabled=False)
            before = snapshot(page, example)
            after = snapshot(page, compact)
            require(before == after, 'Chrome semantic DOM/text/attributes changed for optional dt/dd tags')
            page.set_content(document)
            base_document = page.evaluate("""() => ({html:document.documentElement.outerHTML,
                schema:document.querySelector('script[type="application/ld+json"]').textContent})""")
            page.set_content(compact_document)
            new_document = page.evaluate("""() => ({html:document.documentElement.outerHTML,
                schema:document.querySelector('script[type="application/ld+json"]').textContent})""")
            require(base_document == new_document, 'generated page shell changed Chrome DOM/schema')
            indexes = sorted({0, len(paths)//2, len(paths)-1})
            for index in indexes:
                path = paths[index]
                markup = path.read_text(encoding='utf-8')
                page.set_content(markup)
                result = page.evaluate("""() => ({
                    heading:document.querySelector('h1')?.textContent,
                    main:document.querySelector('main')?.textContent,
                    canonical:document.querySelector('link[rel=canonical]')?.href,
                    source:document.querySelector('section.panel dl')?.textContent,
                    schema:document.querySelector('script[type="application/ld+json"]')?.textContent,
                    scripts:[...document.querySelectorAll('script')].map(x=>x.type)})""")
                require(result['heading'] and result['main'] and result['canonical'] and
                        result['source'] and result['schema'], 'missing rendered source/provenance')
                require(result['scripts'] == ['application/ld+json'],
                        'static reading page unexpectedly requires scripts')
                json.loads(result['schema'])
                checked.append(path.relative_to(site_root).as_posix())
        finally:
            browser.close()
    return {'schema':'hadith-bank-static-dom-browser-v1','status':'passed',
            'source_dom_preserved':True,'javascript_disabled':True,
            'tested_pages':checked,'static_pages_total':len(paths),
            'scope':'synthetic Chromium whole-DOM equality plus three real staged pages; complete per-record normalized source-DOM validation occurs during generator build'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--site-root', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    args=p.parse_args()
    result=run(args.site_root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
