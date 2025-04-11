import os
from collections import defaultdict

# Search directory for relevant PNG files
png_files = [f for f in os.listdir("3_1_3_web") if f.endswith(".png") and f.startswith("3_1_3_acm_")]

# Categorize by day_window (e.g., 3_1_3_acm_1days_match_...)
grouped = defaultdict(list)
for f in png_files:
    parts = f.split("_")
    for i, part in enumerate(parts):
        if part.endswith("days"):
            try:
                key = int(part.replace("days", ""))
                grouped[key].append(f)
            except ValueError:
                continue

# Sort each group by filename
for files in grouped.values():
    files.sort()

# Generate HTML
html_content = """
<html>
<head>
    <title>ACM Match Charts Gallery</title>
    <style>
        body { font-family: sans-serif; }
        h2 { margin-top: 40px; }
        .gallery img { max-width: 100%; height: auto; margin-bottom: 10px; }
    </style>
</head>
<body>
<h1>ACM Match Charts Gallery</h1>
"""

for day_window in sorted(grouped):
    html_content += f"<h2>±{day_window} Days</h2><div class='gallery'>"
    for img_file in grouped[day_window]:
        html_content += f'<div><img src="3_1_3_web/{img_file}" alt="3_1_3_web/{img_file}"><p>3_1_3_web/{img_file}</p></div>\n'
    html_content += "</div>\n"

html_content += "</body></html>"

# Save to HTML file
with open("3_1_3_acm_gallery.html", "w") as f:
    f.write(html_content)

print("Gallery saved to 3_1_3_acm_gallery.html")