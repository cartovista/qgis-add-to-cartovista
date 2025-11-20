from pathlib import Path

def get_oauth_html(title: str, message: str):
    
  plugin_dir = Path(__file__).resolve().parent.parent
  logo_path = plugin_dir / "assets" / "cartovista_logo.svg"
  logo_svg = logo_path.read_text(encoding="utf-8")
  return  f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Authentication successful</title>
  <style>
    body {{
      font-family: sans-serif;
      background: #f6f7f9;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }}
    .card {{
      background: #fff;
      padding: 2rem;
      border-radius: 12px;
      box-shadow: 0 8px 30px rgba(16,24,40,0.08);
      text-align: center;
      max-width: 480px;
    }}
    .logo {{
      margin-bottom: 1rem;
    }}
    .title {{
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0.5rem 0;
    }}
    svg {{
        width: 45%;
        height: fit-content;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="logo">{logo_svg}</div>
    <h1 class="title">{title}</h1>
    <p>{message}</p>
  </div>
</body>
</html>"""

SUCCESS_HTML = get_oauth_html("Authentication successful", "You may now close this window and return to QGIS.")
ERROR_HTML = get_oauth_html("Authentication failed", "We were unable to complete the sign-in process. Please return to QGIS and try again.")
