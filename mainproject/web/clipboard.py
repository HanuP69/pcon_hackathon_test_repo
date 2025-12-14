import sys

IS_WEB = sys.platform == "emscripten"

if IS_WEB:
    try:
        from platform import window
    except ImportError:
        window = None

def copy(text):
   
    print(f"DEBUG: Copying '{text}'") 
    
    if IS_WEB:
        if not window:
            print("ERROR: Window object missing.")
            return

        try:
          
            window.prompt("Press Ctrl+C to copy your seed:", text)
            print("DEBUG: Prompt opened for copy.")
        except Exception as e:
            print(f"ERROR: Web Copy Failed: {e}")



def paste():
    if IS_WEB:
        if not window: return ""
        try:
            text = window.prompt("Paste your seed here (Ctrl+V):", "")
            return text if text is not None else ""
        except:
            return ""
