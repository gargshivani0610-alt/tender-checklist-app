# Streamlit Tender Checklist App
import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

PARAMS_PATH = 'config/parameters.csv'
CIRC_PATH = 'config/circulars.csv'
POLICY_PATH = 'config/policy.csv'
LISTS_PATH = 'config/lists.csv'

@st.cache_data
def load_csv(path, defaults):
    try:
        return pd.read_csv(path)
    except:
        return defaults.copy()

params_df = load_csv(PARAMS_PATH, pd.DataFrame([
    {'Parameter':'Tender ID','Value':'','Help':'Enter a unique identifier'},
    {'Parameter':'Description','Value':'','Help':'Short description'},
    {'Parameter':'Department','Value':'','Help':'LPG/Lube/Engineering/Operations/Retail'},
    {'Parameter':'Tender Type','Value':'','Help':'Service / Works / Goods'},
    {'Parameter':'Tender Platform','Value':'','Help':'GeM or NIC'},
    {'Parameter':'Tender Category','Value':'','Help':'AMC / Lumpsum / LOT'},
    {'Parameter':'Criticality','Value':'','Help':'Critical or Non critical'},
    {'Parameter':'Is Standard Template','Value':'','Help':'Yes = standardized; No = tender-specific'},
    {'Parameter':'Reverse Auction','Value':'','Help':'Yes/No per RA circular'},
    {'Parameter':'Estimate Value (₹)','Value':'','Help':'Numeric total estimate'},
    {'Parameter':'Contract Period (years)','Value':'','Help':'Use 1 for non-AMC/Lumpsum; actual years for AMC'}
]))

circ_df = load_csv(CIRC_PATH, pd.DataFrame([
    {'Parameter':'Is Standard Template','Circular Title':'Standardized Template Policy','Link':'StandardTemplatePolicy.pdf','Effective From':'2025-07-31','Active':'Yes'},
    {'Parameter':'Reverse Auction','Circular Title':'RA Exmeption Circular 16.11.23.pdf','Link':'RA Exmeption Circular 16.11.23.pdf','Effective From':'2023-11-16','Active':'Yes'}
]))

policy_df = load_csv(POLICY_PATH, pd.DataFrame([
    {'RuleKey':'ATO_pct','Threshold':0.60},
    {'RuleKey':'SingleWO_pct','Threshold':0.50},
    {'RuleKey':'TwoWO_pct','Threshold':0.40},
    {'RuleKey':'ThreeWO_pct','Threshold':0.30}
]))

lists_df = load_csv(LISTS_PATH, pd.DataFrame([
    {'ListName':'TenderType','Value':'Service'},
    {'ListName':'TenderType','Value':'Works'},
    {'ListName':'TenderType','Value':'Goods'},
    {'ListName':'Platform','Value':'GeM'},
    {'ListName':'Platform','Value':'NIC'},
    {'ListName':'Category','Value':'AMC'},
    {'ListName':'Category','Value':'Lumpsum'},
    {'ListName':'Category','Value':'LOT'},
    {'ListName':'Criticality','Value':'Critical'},
    {'ListName':'Criticality','Value':'Non critical'},
    {'ListName':'YesNo','Value':'Yes'},
    {'ListName':'YesNo','Value':'No'}
]))

st.set_page_config(page_title='Tender Checklist', page_icon='🧾', layout='wide')
st.title('Tender Checklist - Web App')
mode = st.sidebar.radio('Mode', ['Checklist','Admin'])

def options_for(name):
    return lists_df[lists_df['ListName']==name]['Value'].tolist()

def circular_for(param):
    row = circ_df[(circ_df['Parameter']==param) & (circ_df['Active'].str.lower()=='yes')]
    if len(row):
        r = row.iloc[0]
        return r['Circular Title'], r['Link']
    return None, None

if mode=='Checklist':
    st.subheader('Fill Inputs')
    col1, col2, col3 = st.columns(3)
    with col1:
        tender_id = st.text_input('Tender ID')
        desc = st.text_input('Description')
        dept = st.text_input('Department')
    with col2:
        t_type = st.selectbox('Tender Type', options_for('TenderType'))
        platform = st.selectbox('Tender Platform', options_for('Platform'))
        category = st.selectbox('Tender Category', options_for('Category'))
    with col3:
        criticality = st.selectbox('Criticality', options_for('Criticality'))
        std_template = st.selectbox('Is Standard Template', options_for('YesNo'))
        reverse_auction = st.selectbox('Reverse Auction', options_for('YesNo'))
    est_val = st.number_input('Estimate Value (₹)', min_value=0.0)
    contract_years = st.number_input('Contract Period (years)', min_value=1, value=1)

    annualized = est_val/contract_years if contract_years>1 else est_val
    ato_pct = float(policy_df.loc[policy_df['RuleKey']=='ATO_pct','Threshold'].values[0])
    single_pct = float(policy_df.loc[policy_df['RuleKey']=='SingleWO_pct','Threshold'].values[0])
    two_pct = float(policy_df.loc[policy_df['RuleKey']=='TwoWO_pct','Threshold'].values[0])
    three_pct = float(policy_df.loc[policy_df['RuleKey']=='ThreeWO_pct','Threshold'].values[0])

    st.divider()
    st.subheader('Summary')
    st.write(f'Annualized value: {annualized:,.2f}')
    st.write(f'ATO value: {annualized*ato_pct:,.2f}')
    st.write(f'Single WO: {annualized*single_pct:,.2f}')
    st.write(f'Two WO: {annualized*two_pct:,.2f}')
    st.write(f'Three WO: {annualized*three_pct:,.2f}')

    st.divider()
    st.subheader('Guidelines & Circulars')
    help_std = params_df.loc[params_df['Parameter']=='Is Standard Template','Help'].values[0]
    st.info(f'Is Standard Template — {help_std}')
    title_std, link_std = circular_for('Is Standard Template')
    if link_std:
        st.markdown(f'Circular: [{title_std}]({link_std})')
    help_ra = params_df.loc[params_df['Parameter']=='Reverse Auction','Help'].values[0]
    st.info(f'Reverse Auction — {help_ra}')
    title_ra, link_ra = circular_for('Reverse Auction')
    if link_ra:
        st.markdown(f'Circular: [{title_ra}]({link_ra})')

elif mode=='Admin':
    st.subheader('Manage Circulars & Lists')
    circ_edit = st.data_editor(circ_df, num_rows='dynamic')
    lists_edit = st.data_editor(lists_df, num_rows='dynamic')
    params_edit = st.data_editor(params_df[['Parameter','Help']], num_rows='dynamic')
    if st.button('Save changes'):
        circ_edit.to_csv(CIRC_PATH, index=False)
        lists_edit.to_csv(LISTS_PATH, index=False)
        merged = params_df.copy()
        merged = merged.drop(columns=['Help']).merge(params_edit, on='Parameter', how='left')
        merged.to_csv(PARAMS_PATH, index=False)
        st.success('Saved!')
