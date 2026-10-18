"""Reproducible synthetic holdout evaluation; not real-world attack accuracy."""
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import precision_score,recall_score,f1_score,confusion_matrix
from app.ids import AnomalyModel, FEATURES

def evaluate():
    rng=np.random.default_rng(2026)
    normal=pd.DataFrame({'requests':rng.poisson(12,400)+1,'auth_failures':rng.binomial(2,.10,400),'denials':rng.binomial(2,.08,400),'rate_violations':rng.binomial(1,.02,400)})
    unusual=pd.DataFrame({'requests':rng.integers(70,200,100),'auth_failures':rng.integers(5,30,100),'denials':rng.integers(4,20,100),'rate_violations':rng.integers(2,15,100)})
    data=pd.concat([normal,unusual],ignore_index=True);labels=np.array([0]*400+[1]*100)
    with tempfile.TemporaryDirectory() as directory:
        model=AnomalyModel(Path(directory)/'evaluation.joblib');model.train()
        predictions=np.array([int(model.predict(row)['anomaly_class']==-1) for row in data[FEATURES].to_dict('records')])
    tn,fp,fn,tp=confusion_matrix(labels,predictions).ravel()
    return {'synthetic_only':True,'holdout_seed':2026,'samples':500,'precision':float(precision_score(labels,predictions,zero_division=0)),'recall':float(recall_score(labels,predictions,zero_division=0)),'f1':float(f1_score(labels,predictions,zero_division=0)),'false_positive_rate':float(fp/(fp+tn)),'confusion_matrix':{'tn':int(tn),'fp':int(fp),'fn':int(fn),'tp':int(tp)},'limitation':'Artificial distributions separate normal and unusual traffic strongly; these results do not measure real-world attack detection.'}
if __name__=='__main__':print(json.dumps(evaluate(),indent=2))
