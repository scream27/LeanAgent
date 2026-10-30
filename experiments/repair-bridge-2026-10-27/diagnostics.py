"""Preserve first failure and bounded goals without another model call."""
import re

def diagnostics(log):
    pattern=r'(?m)^(.+?\.lean):(\d+):(\d+): (error|warning|info|information): '
    starts=list(re.finditer(pattern,log));out=[]
    for i,m in enumerate(starts):
        message=log[m.end():starts[i+1].start() if i+1<len(starts) else len(log)].strip()
        if m[4]!='error':continue
        head=message.splitlines()[0] if message else ''
        kind=('unsolved_goals' if 'unsolved goals' in message else
              'heartbeat' if 'heartbeats' in message else
              'solver_no_progress' if any(s in message for s in ['made no progress','could not close','failed']) else
              'unknown_identifier' if 'Unknown identifier' in message or 'unknown identifier' in message else
              'unknown_tactic' if 'unknown tactic' in message else
              'type_mismatch' if 'type mismatch' in message.lower() else 'other')
        out.append({'file':m[1],'line':int(m[2]),'column':int(m[3]),'kind':kind,'head':head,'message':message,
                    'goal_count':len(re.findall(r'(?m)^⊢',message)),
                    'goal_snapshot_trusted':False})
    return out

def bounded_feedback(log,limit=4000):
    rows=diagnostics(log)
    if not rows:return {'status':'no_parsed_errors','raw_tail':log[-limit:]}
    first=rows[0]
    return {'status':'proof_failure','error_count':len(rows),'first_error':{k:v for k,v in first.items() if k!='message'},
            'first_message':first['message'][:limit],'truncated':len(first['message'])>limit,
            'note':'Diagnostic text only; not a replay-certified Lean tactic state.'}
