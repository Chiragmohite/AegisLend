from app.config import Settings
from app.ids import AnomalyModel

if __name__=='__main__':
    s=Settings();m=AnomalyModel(s.ids_model_path,s.ids_anomaly_threshold)
    metadata=m.train()
    print('Trained',metadata['version'],'on',metadata['samples'],'synthetic windows. Restart API to load the artifact.')
