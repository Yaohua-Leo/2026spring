import json

CHECKPOINT_FILE = 'pipeline_checkpoint.json'
CUTOFF_ID = 160

try:
    with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = data.get('processed_chunks', {})
    initial_count = len(chunks)
    
    # Identify keys to remove
    keys_to_remove = [k for k in chunks.keys() if int(k) >= CUTOFF_ID]
    
    for k in keys_to_remove:
        del chunks[k]
        
    data['processed_chunks'] = chunks
    
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Cleaned checkpoint. Removed {len(keys_to_remove)} chunks (IDs >= {CUTOFF_ID}).")
    print(f"Remaining chunks: {len(chunks)}")
    
except Exception as e:
    print(f"Error: {e}")
