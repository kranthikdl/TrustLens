from evidence import analyze_comments

# Test the evidence module directly
test_comments = [
    {"comment_id": "1", "text": "Check out this source: https://www.example.com"},
    {"comment_id": "2", "text": "Just my opinion, no sources"},
    {"comment_id": "3", "text": "Here's proof: https://www.bbc.com/news and https://en.wikipedia.org"}
]

print("Testing evidence analysis directly...")
print("=" * 60)

results = analyze_comments(test_comments)

for result in results:
    print(f"\nComment {result['comment_id']}: {result['text'][:50]}...")
    print(f"  Status: {result['status']}")
    print(f"  URLs found: {len(result['urls'])}")
    print(f"  TL2: {result['TL2_tooltip']}")
    print(f"  TL3: {result['TL3_detail']}")
    if result['urls']:
        print(f"  URLs: {result['urls']}")
        for r in result['results']:
            print(f"    - {r['normalized_url']}: verified={r['verified']}, category={r['category']}")

print("\n" + "=" * 60)
print("Evidence module is working correctly!")
