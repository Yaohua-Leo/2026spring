import os
import time
import json
import fitz  # pymupdf
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration & Setup ---

CONFIG_FILE = "pipeline_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"Warning: {CONFIG_FILE} not found. using defaults.")
    return {}

config = load_config()
api_config = config.get("api_config", {})
pipeline_config = config.get("pipeline_config", {})
paths = config.get("paths", {})

# Load environment variables
load_dotenv(dotenv_path="test_data/.env")

API_KEY = os.getenv("CUSTOM_LLM_API_KEY")
BASE_URL = api_config.get("base_url", "https://api.deepseek.com")
MODEL_NAME = api_config.get("model_name", "deepseek-chat")
CONFIDENCE_THRESHOLD = pipeline_config.get("confidence_threshold", 0.999)
MAX_REPAIR_ATTEMPTS = pipeline_config.get("max_repair_attempts", 3)

PDF_PATH = paths.get("pdf_path", os.path.join("test_data", "I.N. Herstein - Topics in Ring Theory (Lectures in Mathematics) (1969, University of Chicago Press) - libgen.li.pdf"))
MD_PATH = paths.get("md_path", os.path.join("test_data", "I.N.md"))
FINAL_OUTPUT_PATH = paths.get("output_path", "final_validated_output.md")
CHECKPOINT_PATH = paths.get("checkpoint_path", "pipeline_checkpoint.json")

def get_client():
    if not API_KEY:
        print("Error: DEEPSEEK_API_KEY not found in .env")
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

# --- Checkpoint Management ---

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        try:
            with open(CHECKPOINT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"processed_chunks": {}}
    return {"processed_chunks": {}}

def save_checkpoint(checkpoint_data):
    with open(CHECKPOINT_PATH, "w", encoding="utf-8") as f:
        json.dump(checkpoint_data, f, indent=2)

# --- Phase 2: Preprocessing ---

def load_data():
    if not os.path.exists(MD_PATH):
        print(f"Error: MD file not found at {MD_PATH}")
        return None, None
    print(f"Loading MD: {MD_PATH}")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    if not os.path.exists(PDF_PATH):
        print(f"Error: PDF file not found at {PDF_PATH}")
        return md_content, None
        
    print(f"Loading PDF: {PDF_PATH}")
    doc = fitz.open(PDF_PATH)
    return md_content, doc

def split_md_into_chunks(md_content, chunk_size=1500):
    paragraphs = md_content.split("\n\n")
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) > chunk_size:
            chunks.append(current_chunk)
            current_chunk = p
        else:
            if current_chunk:
                current_chunk += "\n\n" + p
            else:
                current_chunk = p
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def safe_chat_completion(client, messages, temperature=0.1):
    """Retry logic for API calls."""
    max_retries = api_config.get("max_retries", 3)
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=temperature,
                stream=False,
                timeout=api_config.get("timeout_seconds", 60)
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"  [API Error] Attempt {attempt+1}/{max_retries}: {e}")
            time.sleep(2 * (attempt + 1))
    return None

# --- Phase 3 & 4: Orchestrator & Specialists ---

def orchestrate_and_verify(client, chunk_id, chunk_text, page_num):
    # 1. Orchestrator
    prompt_orchestrator = f"""
    Analyze the Markdown fragment to determine the best specialist agent for verification.
    
    Fragment (first 500 chars):
    {chunk_text[:500]}...
    
    Return JSON: {{
        "agent_type": "text_forensic" | "formula_auditor" | "layout_architect", 
        "reason": "brief reason"
    }}
    """
    
    messages = [{"role": "system", "content": "You are a Workflow Orchestrator. Output JSON only."},
                {"role": "user", "content": prompt_orchestrator}]
    
    resp_text = safe_chat_completion(client, messages)
    agent_type = "text_forensic" # default
    
    if resp_text:
        try:
            # Simple JSON extraction
            cleaned_json = resp_text.replace("```json", "").replace("```", "").strip()
            decision = json.loads(cleaned_json)
            agent_type = decision.get("agent_type", "text_forensic")
        except:
            pass
        
    # print(f"    -> Route: {agent_type}") # Verbose off

    # 2. Specialist Verification
    # Define agent personas
    personas = {
        "text_forensic": "You are a Text Forensic Agent. Focus on spelling, OCR errors, and semantic coherence.",
        "formula_auditor": "You are a Formula Auditor Agent. Focus on LaTeX syntax, mathematical consistency, and variable definitions.",
        "layout_architect": "You are a Layout Architect Agent. Focus on document structure, headers, and tables.",
        "visual_judge": "You are a Visual Judge. (Simulated text-only mode)"
    }
    
    system_prompt = personas.get(agent_type, personas["text_forensic"])
    
    user_prompt = f"""
    Verify the following markdown content against standard academic/mathematical writing rules (since we don't have the image right now).
    
    Task:
    1. Identify any OCR errors (e.g., '1l' for 'll', 'rn' for 'm').
    2. detailed check of LaTeX formulas if present.
    3. Ensure markdown structure is valid.
    
    Markdown Content:
    {chunk_text}
    
    Return JSON format:
    {{
        "valid": boolean, 
        "confidence": float (0.0-1.0), 
        "issues": "list of specific issues found or 'None'", 
        "corrected_snippet": "the full corrected markdown text (if valid=true also return the text)"
    }}
    """
    
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]
                
    ver_text = safe_chat_completion(client, messages)
    
    try:
        if ver_text:
            cleaned_ver = ver_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_ver)
        else:
            raise Exception("Empty response")
    except:
        # Fallback if XML/JSON parsing fails
        result = {"valid": True, "confidence": 0.5, "issues": "Parse Error in Agent Response", "corrected_snippet": chunk_text}
        
    return result

# --- Phase 6: Refinement ---

def refinement_loop(client, chunk_id, chunk_text, page_num):
    current_text = chunk_text
    attempt = 0
    final_conf = 0.0
    
    while attempt <= MAX_REPAIR_ATTEMPTS:
        # Verify
        result = orchestrate_and_verify(client, chunk_id, current_text, page_num)
        
        conf = result.get("confidence", 0.0)
        final_conf = conf
        
        if conf >= CONFIDENCE_THRESHOLD:
            # Pass
            return result.get("corrected_snippet", current_text), conf, "PASS"
        
        # Fail -> Repair
        attempt += 1
        if attempt > MAX_REPAIR_ATTEMPTS:
            break
            
        print(f"    [Repair] Chunk {chunk_id} Attempt {attempt}/{MAX_REPAIR_ATTEMPTS} (Conf: {conf})")
        issues = result.get("issues", "Unknown issues")
        
        repair_prompt = f"""
        You are a Repair Agent. Fix the following issues in the markdown.
        
        Issues Reported:
        {issues}
        
        Original Markdown:
        {current_text}
        
        Output ONLY the corrected markdown. No explanation.
        """
        
        messages = [
            {"role": "system", "content": "You are a specialized Repair Agent. Return only code."},
            {"role": "user", "content": repair_prompt}
        ]
        
        repaired = safe_chat_completion(client, messages)
        
        if repaired:
             # Strip markdown fences
            clean_repaired = repaired.replace("```markdown", "").replace("```", "").strip()
            current_text = clean_repaired
    
    return current_text, final_conf, "MANUAL_REVIEW"

# --- Main ---

def run_pipeline():
    print("=== Starting Smart MD-PDF Verification Pipeline (Full Doc) ===")
    
    client = get_client()
    if not client:
        return

    md_content, doc = load_data()
    if not md_content:
        return
        
    chunks = split_md_into_chunks(md_content, chunk_size=pipeline_config.get("chunk_size", 1500))
    total_chunks = len(chunks)
    print(f"Total Chunks to Process: {total_chunks}")
    
    # Load Checkpoint
    checkpoint = load_checkpoint()
    processed_map = checkpoint.get("processed_chunks", {})
    
    final_output_list = [None] * total_chunks # Pre-allocate to keep order
    
    # Fill in already processed
    processed_count = 0
    for str_idx, data in processed_map.items():
        idx = int(str_idx)
        if idx < total_chunks:
            final_output_list[idx] = data["content"]
            processed_count += 1
            
    print(f"Resuming... {processed_count}/{total_chunks} already processed.")

    # Process Loop
    for i, chunk in enumerate(chunks):
        if str(i) in processed_map:
            continue # Skip already done
            
        page_num = (i * 2000) // 3000 + 1 # Approximate page number
        
        print(f"Processing Chunk {i+1}/{total_chunks} ({(i+1)/total_chunks*100:.1f}%) ...")
        
        validated_text, conf, status = refinement_loop(client, i, chunk, page_num)
        
        # Save result
        processed_map[str(i)] = {
            "content": validated_text,
            "confidence": conf,
            "status": status
        }
        final_output_list[i] = validated_text
        
        # Update checkpoint
        save_checkpoint({"processed_chunks": processed_map})
        
        # Sleep briefly to avoid aggressive rate limiting
        time.sleep(pipeline_config.get("batch_sleep_seconds", 1))

    # Assemble Final Output
    print("Assembling final document...")
    valid_parts = [p for p in final_output_list if p is not None]
    full_text = "\n\n".join(valid_parts)
    
    with open(FINAL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(full_text)
        
    print(f"=== Success! Output saved to: {FINAL_OUTPUT_PATH} ===")
    print(f"Total Chunks: {total_chunks}")
    print(f"Processed: {len(valid_parts)}")

if __name__ == "__main__":
    run_pipeline()
