import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import signal
import cv2

st.title("Bearing Health Monitoring - Improve Phase Demo")

# DATA UPLOAD

uploaded_file = st.file_uploader("bearing_analysis_dataset.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
else:
    # Simulated data: 50 snapshots with vibration signals
    n = 50
    df = pd.DataFrame({
        'snapshot': range(1, n+1), 
        'rms': np.random.uniform(0.03, 0.09, n),
        'laplacian_variance': np.random.uniform(16000, 18000, n)
    })
    # Add some consecutive highs to demo alert
    df.loc[20:21, 'laplacian_variance'] = [16600, 16700]
    df.loc[35, 'laplacian_variance'] = 16650


# PARAMETERS

threshold = st.slider("Variance Alert Threshold", 16000, 17500, 16500)
consecutive = st.slider("Consecutive Highs Required", 1, 5, 2)

# ASSIGNING CONDITIONS

df['condition'] = pd.cut(
    df['laplacian_variance'],
    bins=[-np.inf, 16500, 17200, np.inf],
    labels=['Healthy', 'Degraded', 'Failing']
)

# REAL_TIME MONITORING LOGIC

alerts = []
high_count = 0
df['alert'] = False

for idx, row in df.iterrows():
    if row['laplacian_variance'] > threshold:
        high_count += 1
        if high_count >= consecutive:
            df.at[idx, 'alert'] = True
            alerts.append(f"ALERT at snapshot {row['snapshot']}: variance = {row['laplacian_variance']:.0f}")
            high_count = 0  # Reset after alert
    else:
        high_count = 0

# DISPLAYING RESULTS

st.subheader("Computed Metrics and Conditions")
st.dataframe(df[['snapshot', 'rms', 'laplacian_variance', 'condition', 'alert']])

st.subheader("Variance Trend with Alerts")
fig = px.line(df, x='snapshot', y='laplacian_variance',
              title='Real-time Laplacian Variance Monitoring',
              labels={'laplacian_variance': 'Variance', 'snapshot': 'Snapshot'})
fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text="Threshold")
fig.add_scatter(x=df[df['alert']]['snapshot'], y=df[df['alert']]['laplacian_variance'],
                mode='markers', marker=dict(color='red', size=12, symbol='star'),
                name='Alert Triggered')
st.plotly_chart(fig)

st.subheader("Triggered Alerts")
if alerts:
    for alert in alerts:
        st.warning(alert)
else:
    st.success("No alerts triggered in this run.")


st.subheader("Before vs After Improvement Summary")
failing_before = len(df[df['condition'] == 'Failing'])
alerts_caught = df['alert'].sum()
prevented_estimate = int(alerts_caught * 0.8)  # assume 80% effectiveness
failing_after = max(0, failing_before - prevented_estimate)

st.metric("Failing snapshots BEFORE improvement", failing_before)
st.metric("Alerts caught early", alerts_caught)
st.metric("Estimated Failing AFTER improvement", failing_after, delta=f"-{prevented_estimate}")
st.write(f"Estimated reduction in critical failures: **{prevented_estimate / failing_before * 100:.1f}%** (simulated)")

st.subheader("Overall Improvement Impact Summary")
failing_before = len(df[df['laplacian_variance'] > 17200])
alerts_caught = df['alert'].sum()
st.write(f"Potential Failing snapshots detected early: **{alerts_caught}**")
st.write(f"Without early alerts, {failing_before} snapshots would have reached critical levels.")
