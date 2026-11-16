"""Writes a SYNTHETIC look-alike of creditcard.csv for smoke-testing the notebook without the real data.
The numbers produced from it mean nothing: fraud is planted in a few columns by a rule written here.
    python tools/make_synthetic_data.py data/creditcard_SYNTHETIC.csv 60000
    CREDITCARD_CSV=data/creditcard_SYNTHETIC.csv   (then run the notebook)"""
import sys
import numpy as np
import pandas as pd

out = sys.argv[1] if len(sys.argv) > 1 else 'data/creditcard_SYNTHETIC.csv'
n = int(sys.argv[2]) if len(sys.argv) > 2 else 60000
rng = np.random.default_rng(7)
t = np.sort(rng.uniform(0, 172792, n))
fraud = rng.random(n) < 0.004
V = rng.standard_normal((n, 28)) * np.linspace(1.9, 0.4, 28)
V[fraud, 13] -= rng.normal(5, 2, fraud.sum())      # V14
V[fraud, 16] -= rng.normal(4, 2, fraud.sum())      # V17
V[fraud, 11] -= rng.normal(3, 2, fraud.sum())      # V12
V[fraud, 3] += rng.normal(2.5, 1.5, fraud.sum())   # V4
amount = np.where(fraud, rng.lognormal(3.6, 1.4, n), rng.lognormal(3.3, 1.3, n)).round(2)
df = pd.DataFrame(V, columns=[f'V{i}' for i in range(1, 29)])
df.insert(0, 'Time', t.round(0))
df['Amount'] = amount
df['Class'] = fraud.astype(int)
df = pd.concat([df, df.sample(40, random_state=1)])          # a few exact duplicates, like the real file
df.to_csv(out, index=False)
print(len(df), 'rows,', int(df['Class'].sum()), 'fraud ->', out)
