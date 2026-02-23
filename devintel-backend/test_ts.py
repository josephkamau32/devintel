import tree_sitter_language_pack as tslp
from tree_sitter import Language, Parser

try:
    lang_name = "python"
    # Try different ways to get the language
    try:
        language = Language(tslp.get_binding(lang_name))
        print(f"Successfully got language for {lang_name} using get_binding")
    except Exception as e:
        print(f"Failed get_binding: {e}")
        try:
            language = tslp.get_language(lang_name)
            print(f"Successfully got language for {lang_name} using get_language")
        except Exception as e2:
            print(f"Failed get_language: {e2}")

    if 'language' in locals():
        parser = Parser(language)
        tree = parser.parse(bytes("def hello():\n    pass", "utf8"))
        print("Successfully parsed code!")
        print(f"Root node type: {tree.root_node.type}")

except Exception as e:
    print(f"Overall error: {e}")
