import ast
import os
import builtins

def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        source = f.read()
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError as e:
        return [f"SyntaxError: {e}"]

    issues = []
    
    # Simple visitor to collect imported names, defined functions, classes, and globals
    class ScopeVisitor(ast.NodeVisitor):
        def __init__(self):
            self.defined = set(dir(builtins))
            self.used = []
            
        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name.split('.')[0]
                self.defined.add(name)
            self.generic_visit(node)
            
        def visit_ImportFrom(self, node):
            for alias in node.names:
                name = alias.asname or alias.name
                self.defined.add(name)
            self.generic_visit(node)
            
        def visit_FunctionDef(self, node):
            self.defined.add(node.name)
            # Check inner function scope
            inner_defined = set(self.defined)
            for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
                inner_defined.add(arg.arg)
            if node.args.vararg:
                inner_defined.add(node.args.vararg.arg)
            if node.args.kwarg:
                inner_defined.add(node.args.kwarg.arg)
                
            for child in ast.walk(node):
                if isinstance(child, ast.Name):
                    if isinstance(child.ctx, ast.Store):
                        inner_defined.add(child.id)
                    elif isinstance(child.ctx, ast.Load):
                        if child.id not in inner_defined:
                            # Might be defined later in module or imported
                            self.used.append((child.id, child.lineno, filepath))
            # Don't recurse generic_visit to avoid duplicate reporting
            
        def visit_AsyncFunctionDef(self, node):
            self.visit_FunctionDef(node)
            
        def visit_ClassDef(self, node):
            self.defined.add(node.name)
            self.generic_visit(node)

    visitor = ScopeVisitor()
    visitor.visit(tree)
    
    # Filter out names that were defined anywhere at top-level
    for name, line, path in visitor.used:
        if name not in visitor.defined:
            issues.append(f"{path}:{line}: Undefined name '{name}'")
            
    return issues

project_dirs = ['config', 'models', 'routes', 'services']
py_files = ['app.py']
for d in project_dirs:
    for root, _, files in os.walk(d):
        for f in files:
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))

all_issues = []
for p in py_files:
    all_issues.extend(check_file(p))

print(f"Scanned {len(py_files)} files. Issues found:")
for iss in all_issues[:30]:
    print(" - ", iss)
if not all_issues:
    print("No undefined names found in functions!")
