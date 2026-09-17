import json, subprocess, os, re, numpy as np, soundfile as sf
from concurrent.futures import ProcessPoolExecutor
FULL='/network/scratch/a/ali.parviz/cosyn_mushra/user_survey_full_20260917'
OUT='/tmp/claude-1340415117/-network-scratch-a-ali-parviz-cosyn-mushra/b6ca8e52-059f-4584-9983-0f56cb7e6a7a/scratchpad/site2'
SR=24000; GAP=0.5; TARGET=-20.0
ALL=['reference_audio','reference_speech','a2s_cascaded','a2s_model_a','a2s_model_b','s2a_cascaded','s2a_ours']
REF=['reference_audio','reference_speech']
full={json.loads(l)['sample_id']:json.loads(l) for l in open(f'{FULL}/samples.jsonl')}
pool=json.load(open('pool50.json'))
EXAMPLE=['7W3cwaYDvJ0','IomFjGmd3FA','1CDjXpp0iEo','Ah4A2GmHay8','aSheN1oz4Io','yGx08kFWCSE','23MER4exl90','LQ7mFn5CvmI']
PRACTICE=['cfXE_kr4Hi4','fSXROtIY4vM']
jobs={}
for x in pool: jobs[x['id']]=('pool',ALL)
for x in pool: jobs.setdefault(x['anchor'],('anchor',REF))
for i in EXAMPLE: jobs[i]=('example',ALL)
for i in PRACTICE: jobs[i]=('practice',ALL)

def load(path):
    raw=subprocess.run(['ffmpeg','-v','error','-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True,check=True).stdout
    x=np.frombuffer(raw,dtype=np.float32).copy()
    m=subprocess.run(['ffmpeg','-v','info','-i',path,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
    mm=re.findall(r'I:\s+(-?[\d.]+) LUFS',m); lufs=float(mm[-1]) if mm else -23.0
    if lufs<-60: lufs=-23.0
    x*=10**((TARGET-lufs)/20); pk=np.max(np.abs(x)) if x.size else 0
    if pk>0.98: x*=0.98/pk
    return x
def build(item):
    sid,(role,clips)=item; r=full[sid]; parts=[]; man={}; t=0.0
    for c in clips:
        x=load(f"{FULL}/{r['files'][c]}"); man[c]=[round(t,3),round(len(x)/SR,3)]; parts+= [x,np.zeros(int(GAP*SR),np.float32)]; t+=len(x)/SR+GAP
    y=np.concatenate(parts); wav=f'{OUT}/audio/{sid}.wav'; mp4=f'{OUT}/audio/{sid}.mp4'
    sf.write(wav,y,SR,subtype='PCM_16'); subprocess.run(['ffmpeg','-v','error','-y','-i',wav,'-c:a','aac','-b:a','64k','-movflags','+faststart',mp4],check=True); os.remove(wav)
    return sid,man,os.path.getsize(mp4)
if __name__=='__main__':
    with ProcessPoolExecutor(16) as ex: res=dict((s,(m,z)) for s,m,z in ex.map(build,list(jobs.items())))
    anchor_of={x['id']:x['anchor'] for x in pool}
    samples=[]
    for sid,(role,_) in jobs.items():
        r=full[sid]; m,z=res[sid]
        samples.append({'id':sid,'role':role,'gender':r['speaker_gender'],'emotion':r['speaker_emotion'],'scene':r['scene_group'],'caption':r['audio_caption'],'text':r['speech_text'],'clips':m,**({'anchor':anchor_of[sid]} if sid in anchor_of else {})})
    json.dump({'sr':SR,'target_lufs':TARGET,'source':'user_survey_full_20260917 + mismatch_pairs.csv','samples':samples},open(f'{OUT}/manifest.json','w'))
    from collections import Counter; print(Counter(j[0] for j in jobs.values()), 'total MB', round(sum(z for _,z in res.values())/1e6,1))
