#!/bin/bash -eu

cd "$SRC"/jupytext
pip3 install .[test-fuzzing]

# Build fuzzers in $OUT
for fuzzer in $(find tests/fuzzing -name '*_fuzzer.py');do
  compile_python_fuzzer "$fuzzer"
done

zip -q $OUT/rw_fuzzer_seed_corpus.zip tests/fuzzing/corpus/*
zip -q $OUT/roundtrip_fuzzer_seed_corpus.zip tests/fuzzing/corpus/*
