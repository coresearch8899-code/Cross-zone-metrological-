import pandas as pd, numpy as np, json
from scipy import stats
d=pd.read_pickle('d_clean.pkl')
pv=lambda c: d.pivot(index='date',columns='z',values=c)
L=pv('daily_load_kwh').sum(axis=1,min_count=3); B=pv('daily_purchased_kwh').sum(axis=1,min_count=3); Y=pv('equivalent_hours'); E=pv('daily_production_kwh')
out={}
for code,dt in [('M1','2024-06-25'),('T1','2026-06-11'),('C3','2024-06-23')]:
    t0=pd.Timestamp(dt)
    for nm,s in [('load',L),('purchased',B)]:
        same=[t0-pd.Timedelta(weeks=k) for k in range(1,7)]
        v=np.log(s.reindex(same)).dropna(); z=(np.log(s[t0])-v.mean())/v.std()
        out[f'{code}_{nm}_day0_vs_sameDOW']={'pct':round(float((s[t0]/np.exp(v.mean())-1)*100),2),'z':round(float(z),2),'weekday':t0.day_name()}
        pre=np.log(s[t0-pd.Timedelta(days=28):t0-pd.Timedelta(days=1)]); post=np.log(s[t0+pd.Timedelta(days=1):t0+pd.Timedelta(days=28)])
        dm=pre.groupby(pre.index.dayofweek).mean(); post_adj=post-post.index.dayofweek.map(dm).values
        diff=post_adj.mean(); se=post_adj.std()/np.sqrt(len(post_adj)); m=0.03; dfree=len(post_adj)-1
        p=max(1-stats.t.cdf((diff+m)/se,dfree), stats.t.cdf((diff-m)/se,dfree))
        out[f'{code}_{nm}_DOWadj_4wk']={'diff_pct':round(float(diff*100),2),'ci95':[round(float((diff-1.96*se)*100),2),round(float((diff+1.96*se)*100),2)],'p_TOST_3pct':round(float(p),4)}
t0=pd.Timestamp('2026-06-11'); rat=np.median((Y[1]/Y[3])[t0-pd.Timedelta(days=7):t0-pd.Timedelta(days=1)])
exp=Y[3][t0]*rat*2256.3; out['T1_z1_expected_kWh']=round(float(exp),1); out['T1_z1_actual_kWh']=round(float(E[1][t0]),1); out['T1_z1_deficit_kWh']=round(float(exp-E[1][t0]),1)
json.dump(out,open('res_grid.json','w'),indent=1)
e=pd.read_csv('event_study.csv'); y=e[(e.metric=='yield-ratio')&e.p_one.notna()&(e.event!='C7')].copy()
y=y.sort_values('p_one'); n=len(y); y['rank']=range(1,n+1); y['q']=(y.p_one*n/y['rank'])[::-1].cummin()[::-1].clip(upper=1)
y[['event','zone','q']].to_csv('bh_q.csv',index=False)
