import json

with open("templates/jee_advanced_template.json", "r") as f:
    tmpl = json.load(f)

print("Q1 bubbles:")
for b in tmpl["questions"]["1"]["bubbles"]:
    print(b)

print("\nQ2 bubbles:")
for b in tmpl["questions"]["2"]["bubbles"]:
    print(b)
