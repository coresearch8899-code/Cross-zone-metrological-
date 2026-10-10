
import pandas as pd, numpy as np, json
from scipy import stats
d=pd.read_pickle('d_clean.pkl'); PRc=pd.read_pickle('PRc.pkl')
Y=d.pivot(index='date',columns='z',values='equivalent_hours').reindex(PRc.index)
yr1=np.log(Y[1]/Y[3]).where(PRc[1].notna()&PRc[3].notna())
R=json.load(open('res_ext.json')); sub=[]
for a,b in [('2026-03-23','2026-06-11'),('2026-06-11','2026-09-05')]:
    A,B=pd.Timestamp(a)+pd.Timedelta(days=5),pd.Timestamp(b)-pd.Timedelta(days=1)
    q=yr1[A:B].dropna(); t=(q.index-q.index[0]).days.values; r=stats.theilslopes(q.values,t,0.95)
    sub.append({'from':a,'to':b,'days':(pd.Timestamp(b)-pd.Timestamp(a)).days,'yr1':[round(float(r.slope)*100,4),round(float(r.low_slope)*100,4),round(float(r.high_slope)*100,4)]})
R['interval_rates_split_T1']=sub; json.dump(R,open('res_ext.json','w'),indent=1,ensure_ascii=False)
