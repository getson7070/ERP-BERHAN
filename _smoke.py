import importlib
erp = importlib.import_module("erp")
create_app = getattr(erp, "create_app")
app = create_app(testing=True) if "testing" in create_app.__code__.co_varnames else create_app()
print("factory OK; socketio=", hasattr(erp, "socketio"))

# Show a quick route table to confirm blueprints are registered
print("\\nROUTES:")
for r in sorted([ (r.rule, ",".join(sorted(r.methods))) for r in app.url_map.iter_rules() ]):
    print(" ", r)

client = app.test_client()
for p in ("/status","/ops/doctor","/mfa/setup"):
    try:
        r = client.get(p)
        print(p, "->", r.status_code)
    except Exception as e:
        print(p, "-> ERROR", e)
