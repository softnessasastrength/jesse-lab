#!/usr/bin/env python3
import argparse,json,pathlib,sys,os

def main():
    p=argparse.ArgumentParser();p.add_argument('baseline');p.add_argument('candidate');p.add_argument('--out',required=True);a=p.parse_args()
    b=json.loads(pathlib.Path(a.baseline).read_text());c=json.loads(pathlib.Path(a.candidate).read_text())
    def index(d):
        rows=d['results']; ids=[r['case']['id'] for r in rows]
        if len(set(ids))!=len(ids): raise ValueError('Duplicate case IDs')
        return {r['case']['id']:r for r in rows}
    x,y=index(b),index(c)
    if x.keys()!=y.keys(): raise ValueError('Case IDs differ; comparison stopped')
    lines=['# Baseline vs adapter','Human review required; model judgments are fallible. Different inference runtimes and settings can affect comparisons.','']
    for k in x:
        if x[k]['case']!=y[k]['case']: raise ValueError('Case content differs: '+k)
        lines += ['## '+k,'Safety case: '+str(x[k]['case'].get('safety',False)),'### Baseline',x[k]['response'],'### Baseline evaluation',x[k].get('evaluation','(none)'),'### Adapter',y[k]['response'],'### Adapter evaluation',y[k].get('evaluation','(none)'),'### Human review','- [ ] Reviewed fidelity and safety','']
    out=pathlib.Path(a.out)
    if out.exists(): raise ValueError('Output already exists')
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text('\n'.join(lines));os.chmod(out,0o600);print('Saved',out)
if __name__=='__main__':
    try: main()
    except Exception as exc: print('Error:',exc,file=sys.stderr);sys.exit(1)
