import difflib
import os
import re

FILE_A = "final_validated_output.md"
FILE_B = "Golden_Herstein.md"

def count_latex(text):
    inline = len(re.findall(r'(?<!\$)\$(?!\$)', text)) # Single $
    display = len(re.findall(r'\$\$', text)) # Double $$
    return inline // 2, display // 2 # Rough pair count

def compare_files():
    if not os.path.exists(FILE_A) or not os.path.exists(FILE_B):
        print(f"Error: Files not found. A: {os.path.exists(FILE_A)}, B: {os.path.exists(FILE_B)}")
        return

    print(f"Loading {FILE_A}...")
    with open(FILE_A, 'r', encoding='utf-8') as f:
        text_a = f.read()

    print(f"Loading {FILE_B}...")
    with open(FILE_B, 'r', encoding='utf-8') as f:
        text_b = f.read()

    with open("comparison_result.txt", "w", encoding="utf-8") as out:
        import sys
        sys.stdout = out
        
        # 1. Basic Stats
        print("\n--- Basic Statistics ---")
        print(f"{'Metric':<20} | {'Generated (A)':<15} | {'Reference (B)':<15} | {'Delta':<10}")
        print("-" * 70)
        
        len_a, len_b = len(text_a), len(text_b)
        lines_a, lines_b = len(text_a.splitlines()), len(text_b.splitlines())
        math_a = count_latex(text_a)
        math_b = count_latex(text_b)
        
        print(f"{'Characters':<20} | {len_a:<15} | {len_b:<15} | {len_a - len_b:<10}")
        print(f"{'Lines':<20} | {lines_a:<15} | {lines_b:<15} | {lines_a - lines_b:<10}")
        print(f"{'Inline Math ($)':<20} | {math_a[0]:<15} | {math_b[0]:<15} | {math_a[0] - math_b[0]:<10}")
        print(f"{'Display Math ($$)':<20} | {math_a[1]:<15} | {math_b[1]:<15} | {math_a[1] - math_b[1]:<10}")

        # 2. Similarity (Sampled for Speed)
        print("\n--- Similarity Metrics (First 15k Chars) ---")
        sample_size = 15000
        matcher = difflib.SequenceMatcher(None, text_a[:sample_size], text_b[:sample_size])
        similarity = matcher.ratio()
        print(f"Sample Similarity Score: {similarity*100:.2f}%")
        
        # 3. Sample Diff
        print("\n--- Structural Diff Sample (First 20 Lines) ---")
        diff = difflib.unified_diff(
            text_a.splitlines()[:20], 
            text_b.splitlines()[:20], 
            fromfile='Generated', 
            tofile='Reference', 
            lineterm=''
        )
        for line in diff:
            print(line)

if __name__ == "__main__":
    compare_files()
