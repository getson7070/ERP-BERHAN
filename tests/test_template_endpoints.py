import os, re, glob
from flask import current_app
def iter_eps(root):
    pat = re.compile(r"url_for\(\s*['\"]([\w\.]+)['\"]")
    for path in glob.glob(os.path.join(root, '**', '*.html'), recursive=True):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            for m in pat.finditer(f.read()):
                yield path, m.group(1)
def test_all_template_endpoints_exist(app):
    with app.app_context():
        missing = []
        views = set(current_app.view_functions.keys())
        troot = os.path.join(current_app.root_path, 'templates')
        for path, ep in iter_eps(troot):
            if ep not in views:
                missing.append((os.path.relpath(path, troot), ep))
        assert not missing, 'Missing endpoints: ' + str(missing)