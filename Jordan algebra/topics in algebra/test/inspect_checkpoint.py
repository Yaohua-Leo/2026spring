import json

try:
    with open('pipeline_checkpoint.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    chunks = data.get('processed_chunks', {})
    sorted_ids = sorted([int(k) for k in chunks.keys()])
    
    with open('checkpoint_report.txt', 'w', encoding='utf-8') as out:
        import sys
        sys.stdout = out
        print(f"Total processed chunks: {len(sorted_ids)}")
        
        # Check range 160 to end
        start_check = 160
        found_failure = False
        
        print(f"\n--- Checking chunks {start_check} to {sorted_ids[-1]} ---")
        for cid in sorted_ids:
            if cid < start_check:
                continue
                
            chunk = chunks[str(cid)]
            status = chunk.get('status', 'UNKNOWN')
            conf = chunk.get('confidence', 0.0)
            
            print(f"Chunk {cid}: Status={status}, Conf={conf}")
        
except Exception as e:
    print(f"Error: {e}")
