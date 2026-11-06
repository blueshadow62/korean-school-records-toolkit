"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { createReport, countNeisBytes, countLines } = require("./korean_character_count.js");

test("mixed Korean/ASCII/emoji graphemes", () => {
  const r = createReport("가A🙂", "neis").counts;
  assert.equal(r.characters, 3);
  assert.equal(r.bytes_utf8, 8);
  assert.equal(r.bytes_neis, 8); // 3 + 1 + 4 (emoji falls back to UTF-8)
});

test("line breaks: CRLF is one break and one NEIS byte", () => {
  assert.equal(countLines("a\r\nb"), 2);
  assert.equal(countNeisBytes("가\r\n나"), 7);
  assert.equal(countNeisBytes("가\n나"), 7);
  assert.equal(countNeisBytes("가\u2028나"), 7);
});

test("whitespace and empty input", () => {
  assert.equal(countLines(""), 0);
  assert.equal(createReport("  자료를  비교함  ").counts.characters_without_whitespace, 6);
});
