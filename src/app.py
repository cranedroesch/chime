import pandas as pd  # type: ignore
import streamlit as st  # type: ignore
import numpy as np  # type: ignore
import matplotlib  # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # type: ignore

from constants import (
    DELAWARE, CHESTER, MONTGOMERY, BUCKS, PHILLY, S_DEFAULT, KNOWN_INFECTIONS
)
from sidebar import (
    _initial_infections, _current_hosp, _doubling_time, _hosp_rate, _icu_rate, _vent_rate,
    _hosp_los, _icu_los, _vent_los, _Penn_market_share, _S, _total_infections, _detection_prob,
    _los_dict
)
from markdown import (show_more_info_about_this_tool)
from model import (
    model,
)

hide_menu_style = """
       <style>
       #MainMenu {visibility: hidden;}
       </style>
       """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title("COVID-19 Hospital Impact Model for Epidemics")
st.markdown(
    """*This tool was developed by the [Predictive Healthcare team](http://predictivehealthcare.pennmedicine.org/) at Penn Medicine. For questions and comments please see our [contact page](http://predictivehealthcare.pennmedicine.org/contact/).*"""
)


# Get the input
initial_infections = _initial_infections()
current_hosp = _current_hosp()
doubling_time = _doubling_time()
hosp_rate = _hosp_rate()
icu_rate = _icu_rate()
vent_rate = _vent_rate()
hosp_los = _hosp_los()
icu_los = _icu_los()
vent_los = _vent_los()
Penn_market_share = _Penn_market_share()
S = _S()

detection_prob = _detection_prob(initial_infections, current_hosp, Penn_market_share, hosp_rate)
if st.checkbox("Show more info about this tool"):
    show_more_info_about_this_tool(initial_infections, detection_prob)

n_days = st.slider("Number of days to project", 30, 200, 60, 1, "%i")


st.subheader("New Admissions")
st.markdown("Projected number of **daily** COVID-19 admissions at Penn hospitals")


projection, s, i, r = model(
    initial_infections=initial_infections,
    detection_prob=detection_prob,
    doubling_time=doubling_time,
    n_days=n_days,
    hosp_rate=hosp_rate,
    icu_rate=icu_rate,
    vent_rate=vent_rate,
    Penn_market_share=Penn_market_share,
    S=S
)

# New cases
projection_admits = projection.iloc[:-1, :] - projection.shift(1)
projection_admits[projection_admits < 0] = 0

plot_projection_days = n_days - 10
projection_admits["day"] = range(projection_admits.shape[0])

fig, ax = plt.subplots(1, 1, figsize=(10, 4))
ax.plot(
    projection_admits.head(plot_projection_days)["hosp"], ".-", label="Hospitalized"
)
ax.plot(projection_admits.head(plot_projection_days)["icu"], ".-", label="ICU")
ax.plot(projection_admits.head(plot_projection_days)["vent"], ".-", label="Ventilated")
ax.legend(loc=0)
ax.set_xlabel("Days from today")
ax.grid("on")
ax.set_ylabel("Daily Admissions")
st.pyplot()

admits_table = projection_admits[np.mod(projection_admits.index, 7) == 0].copy()
admits_table["day"] = admits_table.index
admits_table.index = range(admits_table.shape[0])
admits_table = admits_table.fillna(0).astype(int)

if st.checkbox("Show Projected Admissions in tabular form"):
    st.dataframe(admits_table)

st.subheader("Admitted Patients (Census)")
st.markdown(
    "Projected **census** of COVID-19 patients, accounting for arrivals and discharges at Penn hospitals"
)

# ALOS for each category of COVID-19 case (total guesses)

fig, ax = plt.subplots(1, 1, figsize=(10, 4))

census_dict = {}
for k, los in _los_dict(hosp_los, icu_los, vent_los).items():
    census = (
        projection_admits.cumsum().iloc[:-los, :]
        - projection_admits.cumsum().shift(los).fillna(0)
    ).apply(np.ceil)
    census_dict[k] = census[k]
    ax.plot(census.head(plot_projection_days)[k], ".-", label=k + " census")
    ax.legend(loc=0)

ax.set_xlabel("Days from today")
ax.grid("on")
ax.set_ylabel("Census")
st.pyplot()

census_df = pd.DataFrame(census_dict)
census_df["day"] = census_df.index
census_df = census_df[["day", "hosp", "icu", "vent"]]

census_table = census_df[np.mod(census_df.index, 7) == 0].copy()
census_table.index = range(census_table.shape[0])
census_table.loc[0, :] = 0
census_table = census_table.dropna().astype(int)

if st.checkbox("Show Projected Census in tabular form"):
    st.dataframe(census_table)

st.markdown(
    """**Click the checkbox below to view additional data generated by this simulation**"""
)
if st.checkbox("Show Additional Projections"):
    st.subheader(
        "The number of infected and recovered individuals in the hospital catchment region at any given moment"
    )
    fig, ax = plt.subplots(1, 1, figsize=(10, 4))
    ax.plot(i, label="Infected")
    ax.plot(r, label="Recovered")
    ax.legend(loc=0)
    ax.set_xlabel("days from today")
    ax.set_ylabel("Case Volume")
    ax.grid("on")
    st.pyplot()

    # Show data
    days = np.array(range(0, n_days + 1))
    data_list = [days, s, i, r]
    data_dict = dict(zip(["day", "susceptible", "infections", "recovered"], data_list))
    projection_area = pd.DataFrame.from_dict(data_dict)
    infect_table = (projection_area.iloc[::7, :]).apply(np.floor)
    infect_table.index = range(infect_table.shape[0])

    if st.checkbox("Show Raw SIR Similation Data"):
        st.dataframe(infect_table)

st.subheader("References & Acknowledgements")
st.markdown(
    """* AHA Webinar, Feb 26, James Lawler, MD, an associate professor University of Nebraska Medical Center, What Healthcare Leaders Need To Know: Preparing for the COVID-19
* We would like to recognize the valuable assistance in consultation and review of model assumptions by Michael Z. Levy, PhD, Associate Professor of Epidemiology, Department of Biostatistics, Epidemiology and Informatics at the Perelman School of Medicine 
    """
)
st.markdown("© 2020, The Trustees of the University of Pennsylvania")
