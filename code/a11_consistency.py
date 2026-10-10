"""Step 11 (R5): temporal-consistency audit of record, events, extraction and analysis dates."""
import pandas as pd, json, re
raw = pd.read_csv('daily.csv'); raw['date'] = pd.to_datetime(raw.date)
d = pd.read_pickle('d_clean.pkl'); PRc = pd.read_pickle('PRc.pkl')
out = {}
first, last = d.date.min(), d.date.max()
cal = pd.date_range(first, last); obs = pd.DatetimeIndex(sorted(d.date.unique()))
out['first_day'] = str(first.date()); out['last_day'] = str(last.date())
out['calendar_days'] = len(cal); out['observed_days'] = len(obs); out['missing_days'] = [str(x.date()) for x in cal.difference(obs)]
out['zone_days_raw'] = len(raw); out['zone_days_after_dedup'] = len(d); out['zone_days_per_zone'] = d.groupby('z').size().to_dict()
out['all_zones_same_span'] = bool(d.groupby('z').date.agg(['min', 'max']).nunique().max() == 1)
ex = raw.source_file.str.extract(r'_(\d{14})\.xlsx')[0]
exd = pd.to_datetime(ex, format='%Y%m%d%H%M%S')
out['extraction_dates'] = sorted({str(x.date()) for x in exd}); out['n_export_files'] = int(exd.nunique()); out['last_export'] = str(exd.max())
out['extraction_after_last_record_day'] = bool(exd.max() > last)
per_file = raw.assign(ex=exd).groupby('ex').date.agg(['min', 'max', 'count'])
out['records_dated_on_or_after_their_export_day'] = int((raw.date >= exd.dt.normalize()).sum())
out['last_day_n_intervals'] = raw[raw.date == last].n_intervals.tolist()
out['incomplete_days_n_intervals_lt48'] = int((d.n_intervals < 48).sum())
out['analysis_window_start'] = str(PRc.index.min().date()); out['analysis_window_end'] = str(PRc.index.max().date())
out['merge_date'] = '2026-09-09'; out['analysis_period'] = '2026-09-09 to 2026-10-08'
EV = {'C1': ('2023-05-06', '6 May 2566 BE'), 'C2': ('2024-03-09', '9 Mar 2567 BE'), 'C3': ('2024-06-23', '23 Jun 2567 BE'),
      'M1': ('2024-06-25', '25 Jun 2567 BE'), 'C4': ('2025-04-25', '25 Apr 2568 BE'), 'C5': ('2025-12-26', '26 Dec 2568 BE'),
      'C6': ('2026-03-23', '23 Mar 2569 BE'), 'T1': ('2026-06-11', '11 Jun 2569 BE'), 'C7': ('2026-09-05', '5 Sep 2569 BE')}
ev = {}
for k, (g, be) in EV.items():
    t = pd.Timestamp(g)
    pre = PRc[t - pd.Timedelta(days=14): t - pd.Timedelta(days=1)][1].notna().sum(); post = PRc[t + pd.Timedelta(days=4): t + pd.Timedelta(days=17)][1].notna().sum()
    ev[k] = {'gregorian': g, 'log_entry_BE': be, 'inside_record': bool(first <= t <= last), 'inside_analysis_window': bool(PRc.index.min() <= t <= PRc.index.max()),
             'days_before_cutoff': int((last - t).days), 'valid_pre_days_z1': int(pre), 'valid_post_days_z1': int(post), 'testable': bool(pre >= 6 and post >= 6)}
out['events'] = ev
# event dates vs BE conversion (BE = CE + 543)
out['BE_conversion_ok'] = all(int(re.search(r'(\d{4}) BE', v[1]).group(1)) - 543 == int(v[0][:4]) for v in EV.values())
json.dump(out, open('res_consistency.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
