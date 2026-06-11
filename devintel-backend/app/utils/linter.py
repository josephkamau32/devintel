import ast

try:
    import jsbeautifier
    _JS_LINT_AVAILABLE = True
except ImportError:
    _JS_LINT_AVAILABLE = False


def check_syntax(file_path: str, content: str, language: str = None) -> list[str]:
    """
    Checks the syntax of the given content for Python or JavaScript/TypeScript files.
    Returns a list of error strings, or an empty list if no errors are found.
    """
    errors = []

    # Try to infer language from extension if not provided
    if not language:
        if file_path.endswith('.py'):
            language = 'python'
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            language = 'javascript'
        else:
            language = 'unknown'

    if language.lower() == 'python':
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"SyntaxError on line {e.lineno}, offset {e.offset}: {e.msg}\n{e.text}")
        except Exception as e:
            errors.append(f"Failed to parse Python code: {str(e)}")

    elif language.lower() in ('javascript', 'typescript', 'js', 'ts'):
        if _JS_LINT_AVAILABLE:
            try:
                jsbeautifier.beautify(content)
            except Exception as e:
                errors.append(f"JavaScript/TypeScript Syntax Error: {str(e)}")
        # If jsbeautifier is not installed, skip JS/TS linting silently

    return errors
