How to run the standalone heuristics demo

1) Save heuristic_model.py in the same folder as these sample files (or anywhere on your PATH).

2) Quick run with a couple of inline texts:
   python heuristic_model.py --text "According to the meta-analysis (doi:10.1038/abcd1234), p < .01" "I think this is true, source: trust me bro" --pretty

3) Run on the provided sample file and print to screen:
   python heuristic_model.py --infile comments.txt --pretty

4) Run on the sample file and write JSON output to heuristics_output.json:
   python heuristic_model.py --infile comments.txt --out heuristics_output.json --pretty

Files in this folder:
- comments.txt       : one comment per line
- comments.json      : same comments as JSON with a 'texts' array
- heuristics_sample_README.txt : this instruction file
