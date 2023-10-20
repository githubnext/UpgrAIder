from upgraider.Model import fix_suggested_code, UpdateStatus 
import sys
import textwrap

def create_comment(reason: str) -> str:
    lines = textwrap.wrap(reason, width=80)
    lines = ["# " + line for line in lines]
    return "\n".join(lines)

def main():
    code = sys.stdin.read()
    prompt_text, model_response, parsed_response, ref_count= fix_suggested_code(code, model="gpt-4")

    # stdout will be empty if there is no update
    if (parsed_response.update_status == UpdateStatus.NO_UPDATE):
        return
    
    if parsed_response.reason is not None:
        print("# I updated this code for you because:")
        print(create_comment(parsed_response.reason))
        
    print(parsed_response.updated_code)

if __name__ == "__main__":
    main()