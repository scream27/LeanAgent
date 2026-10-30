"""Translate the existing repair-policy response contract; never invoke a model."""
import json

def repair_response_to_common(response):
    status=response.get('status')
    if status in {'need_context','no_candidate'}:
        return {'kind':'control','status':status,'required_context':response.get('required_context',[])}
    if status!='candidate' or not isinstance(response.get('proof_body'),str) or not response['proof_body'].strip():
        raise ValueError('Expected non-empty candidate proof_body or a recognized control status')
    return {'kind':'candidate','content':json.dumps({'proof':response['proof_body']},ensure_ascii=False)}
