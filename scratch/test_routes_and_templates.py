import sys
import os
sys.path.insert(0, os.path.abspath('.'))
import jinja2

os.environ['TESTING'] = '1'

def test_jinja_templates():
    print("Testing Jinja2 template compilation...")
    template_dir = os.path.abspath("templates")
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
    
    errors = []
    for root, dirs, files in os.walk(template_dir):
        for f in files:
            if f.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, f), template_dir).replace('\\', '/')
                try:
                    env.get_template(rel_path)
                except jinja2.TemplateSyntaxError as e:
                    errors.append(f"Template Syntax Error in {rel_path} line {e.lineno}: {e.message}")
                except Exception as e:
                    errors.append(f"Template Error in {rel_path}: {str(e)}")
                    
    if errors:
        print(f"FAILED: Found {len(errors)} template errors:")
        for err in errors:
            print("  - " + err)
    else:
        print("SUCCESS: All HTML templates compiled with 0 Jinja syntax errors.")
    return len(errors) == 0

def test_flask_routes():
    print("\nTesting Flask routes and blueprint registrations...")
    from app import app
    client = app.test_client()
    
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append((rule.rule, list(rule.methods), rule.endpoint))
    
    print(f"Total registered routes: {len(routes)}")
    
    # Test public GET endpoints to verify no 500 crashes
    test_urls = [
        '/',
        '/login',
        '/register',
        '/book',
        '/book/walkin',
        '/walk-in',
        '/order/track',
        '/api/lobby/machines',
        '/api/lobby/traffic',
        '/api/order/track?order_code=ORD-99999',
        '/api/health',
        '/api/rates'
    ]
    
    route_errors = []
    for url in test_urls:
        try:
            resp = client.get(url)
            print(f"GET {url:40s} -> Status {resp.status_code}")
            if resp.status_code >= 500:
                route_errors.append(f"500 Internal Server Error on GET {url}")
        except Exception as e:
            route_errors.append(f"Exception on GET {url}: {e}")
            
    if route_errors:
        print(f"FAILED: Found {len(route_errors)} route errors:")
        for err in route_errors:
            print("  - " + err)
    else:
        print("SUCCESS: Key GET endpoints responded cleanly without 500 errors.")
    return len(route_errors) == 0

def test_db_models():
    print("\nTesting SQLAlchemy models and Session...")
    from config.database import SessionLocal, engine
    from models.schemas import Base, Appointment, Queue, MachineStatus, User
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        # Test basic queries
        db.query(Appointment).count()
        db.query(Queue).count()
        db.query(MachineStatus).count()
        db.query(User).count()
        print("SUCCESS: Database models and queries execute cleanly.")
        return True
    except Exception as e:
        print(f"FAILED: Database query error: {e}")
        return False
    finally:
        db.close()

if __name__ == '__main__':
    t1 = test_jinja_templates()
    t2 = test_flask_routes()
    t3 = test_db_models()
    if t1 and t2 and t3:
        print("\n=== ALL SYSTEM AUDIT CHECKS PASSED ===")
        sys.exit(0)
    else:
        print("\n=== ISSUES DETECTED ===")
        sys.exit(1)
