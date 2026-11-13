#!/usr/bin/env node
"use strict";

// Derive disposable reader indexes from the exact browser functions.  Only the
// explicitly delimited pure declarations below are evaluated, never the page.
const fs = require("node:fs");
const path = require("node:path");
const readline = require("node:readline");
const {once} = require("node:events");

const BLOCKS = [
  ["const fold =", "const element ="],
  ["const sourceURL =", "const sourceLabel ="],
  ["const originCategory =", "const originLabel ="],
  ["const counterpartData =", "const matchesCounterpartAvailability ="],
  ["const isOCR =", "const reviewBadges ="],
  ["const hasNoncanonicalNumbering =", "const numberLabel ="],
  ["const availableLanguageCodes =", "const materialSummary ="],
  ["const primarySearchFields=", "const citationPairKeys="],
  ["const searchStrings =", "const counterpartCitation ="],
  ["const versionSearchValues =", "const sameReadingLanguage ="],
  ["const primarySearchKey =", "const searchKeys ="],
  ["const annotationSearchKey =", "let commentaryKeys ="],
];

function projectionSource(template) {
  return BLOCKS.map(([start, end]) => {
    const begin = template.indexOf(start);
    const finish = template.indexOf(end, begin + start.length);
    if (begin < 0 || finish < begin || template.indexOf(start, begin + start.length) >= 0) {
      throw new Error("Reader projection declaration boundary missing or ambiguous: " + start);
    }
    return template.slice(begin, finish);
  }).join("\n");
}

function createProjector(template) {
  const factory = new Function(projectionSource(template) + `
    return function project(record, detail) {
      if (!record || typeof record !== "object" || Array.isArray(record)) {
        throw new Error("Reader projection requires a record object");
      }
      if (Object.prototype.hasOwnProperty.call(record, "_reader")) {
        throw new Error("Canonical reader record uses reserved _reader field");
      }
      if (!Array.isArray(detail) || detail.length !== 2 ||
          !Number.isSafeInteger(detail[0]) || detail[0] < 0 ||
          !Number.isSafeInteger(detail[1]) || detail[1] <= 0 ||
          !Number.isSafeInteger(detail[0] + detail[1])) {
        throw new Error("Reader projection requires a safe exact byte span");
      }
      const directory = {};
      for (const key of ["id", "language", "book_key", "edition", "source_id"]) {
        if (typeof record[key] !== "string" || !record[key]) {
          throw new Error("Reader projection requires string " + key);
        }
        directory[key] = record[key];
      }
      directory._reader = {
        languages: availableLanguageCodes(record),
        origin: originCategory(record),
        availability: counterpartAvailability(record),
        ocr_pending: needsOCRReview(record),
        citation_pairs: [...recordCitationPairs(record)],
        detail: [...detail],
      };
      return [directory, primarySearchKey(record), annotationSearchKey(record)];
    };
  `);
  return factory();
}

async function streamProjection(templatePath, input = process.stdin, output = process.stdout) {
  const project = createProjector(fs.readFileSync(templatePath, "utf8"));
  const lines = readline.createInterface({input, crlfDelay: Infinity});
  let ordinal = 0, offset = 0;
  for await (const line of lines) {
    if (!line) throw new Error("Empty input row at ordinal " + ordinal);
    const length = Buffer.byteLength(line, "utf8") + 1;
    if (!Number.isSafeInteger(offset + length)) throw new Error("Reader detail offsets exceed safe integer range");
    const record = JSON.parse(line);
    const projected = project(record, [offset, length]);
    const row = JSON.stringify([ordinal, ...projected]) + "\n";
    if (!output.write(row)) await once(output, "drain");
    offset += length;
    ordinal++;
  }
}

module.exports = {createProjector, projectionSource, streamProjection};

if (require.main === module) {
  const templatePath = process.argv[2] || path.join(__dirname, "..", "reader", "template.html");
  streamProjection(templatePath).catch(error => {
    // Keep diagnostics bounded and never print source records or a stack body.
    process.stderr.write("Reader projection failed: " + String(error.message || error).slice(0,1000) + "\n");
    process.exitCode = 1;
    // A parsing/template failure must not keep stdin alive while the producer
    // is blocked writing a later record into a pipe nobody will drain.
    process.stdin.destroy();
  });
}

