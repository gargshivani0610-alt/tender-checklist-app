# Streamlit Tender Checklist App
import os
import shutil
import streamlit as st
import pandas as pd
from datetime import datetime

# Paths
CONFIG_DIR = 'config'
PARAMS_PATH = os.path.join(CONFIG_DIR, 'parameters.csv')
CIRC_PATH = os.path.join(CONFIG_DIR, 'circulars.csv')
POLICY_PATH = os.path.join(CONFIG_DIR, 'policy.csv')
LISTS_PATH = os.path.join(CONFIG_DIR, 'lists.csv')
BACKUP_ROOT = os.path.join(CONFIG_DIR, 'backups')

# Ensure config and migrate stray CSVs from repo root into config/
def ensure_config_and_move():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    moved = []
    for fname in ['parameters.csv', 'circulars.csv', 'policy.csv', 'lists.csv']:
        src = os.path.join('.', fname)
        dst = os.path.join(CONFIG_DIR, fname)
        try:
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.move(src, dst)
                moved.append(fname)
        except Exception as e:
            st.warning(f'Could not move {src} to {dst}: {e}')
    if moved:
        st.info(f"Moved existing CSVs into {CONFIG_DIR}/: {', '.join(moved)}")

def ensure_backup_dir():
    os.makedirs(BACKUP_ROOT, exist_ok=True)

def backup_file(path):
    """Copy existing file into backups/<timestamp>/filename and return backup path."""
    ensure_backup_dir()
    if not os.path.exists(path):
        return None
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    dest_dir = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(dest_dir, exist_ok=True)
    fname = os.path.basename(path)
    dst = os.path.join(dest_dir, fname)
    try:
        shutil.copy2(path, dst)
        return dst
    except Exception as e:
        st.warning(f'Failed to create backup for {path}: {e}')
        return None

@st.cache_data
def load_csv(path, defaults):
    try:
        return pd.read_csv(path)
    except Exception:
        return defaults.copy()

# Run migration before loading any CSVs
ensure_config_and_move()

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
    row = circ_df[(circ_df['Parameter']==param) & (circ_df['Active'].astype(str).str.lower()=='yes')]
    if len(row):
        r = row.iloc[0]
        return r.get('Circular Title', None), r.get('Link', None)
    return None, None

# Helper to show help text and circular link for a parameter
def show_help_for(param):
    try:
        help_text = params_df.loc[params_df['Parameter']==param,'Help'].values[0]
    except Exception:
        help_text = ''
    title, link = circular_for(param)
    if help_text:
        st.info(f"{param} — {help_text}")
    else:
        st.info(f"{param} — No help text available")
    if link:
        st.markdown(f"Circular: [{title}]({link})")

if mode=='Checklist':
    st.subheader('Fill Inputs')
    # Use columns and place a small help button beside each dropdown
    col1, col2, col3 = st.columns(3)
    with col1:
        tender_id = st.text_input('Tender ID')
        desc = st.text_input('Description')
        dept = st.text_input('Department')
    with col2:
        # Tender Type with help
        c1, c2 = st.columns([8,1])
        with c1:
            t_type = st.selectbox('Tender Type', options_for('TenderType'))
        with c2:
            if st.button('?', key='help_t_type'):
                show_help_for('Tender Type')

        c3, c4 = st.columns([8,1])
        with c3:
            platform = st.selectbox('Tender Platform', options_for('Platform'))
        with c4:
            if st.button('?', key='help_platform'):
                show_help_for('Tender Platform')

        c5, c6 = st.columns([8,1])
        with c5:
            category = st.selectbox('Tender Category', options_for('Category'))
        with c6:
            if st.button('?', key='help_category'):
                show_help_for('Tender Category')
    with col3:
        c7, c8 = st.columns([8,1])
        with c7:
            criticality = st.selectbox('Criticality', options_for('Criticality'))
        with c8:
            if st.button('?', key='help_criticality'):
                show_help_for('Criticality')

        c9, c10 = st.columns([8,1])
        with c9:
            std_template = st.selectbox('Is Standard Template', options_for('YesNo'))
        with c10:
            if st.button('?', key='help_std_template'):
                show_help_for('Is Standard Template')

        c11, c12 = st.columns([8,1])
        with c11:
            reverse_auction = st.selectbox('Reverse Auction', options_for('YesNo'))
        with c12:
            if st.button('?', key='help_reverse_auction'):
                show_help_for('Reverse Auction')

    est_val = st.number_input('Estimate Value (₹)', min_value=0.0)
    contract_years = st.number_input('Contract Period (years)', min_value=1, value=1)

    annualized = est_val/contract_years if contract_years>1 else est_val

    # Safely pull thresholds (provide defaults if missing)
    def get_threshold(key, default):
        try:
            return float(policy_df.loc[policy_df['RuleKey']==key,'Threshold'].values[0])
        except Exception:
            return default

    ato_pct = get_threshold('ATO_pct', 0.60)
    single_pct = get_threshold('SingleWO_pct', 0.50)
    two_pct = get_threshold('TwoWO_pct', 0.40)
    three_pct = get_threshold('ThreeWO_pct', 0.30)

    st.divider()
    st.subheader('Summary')
    st.write(f'Annualized value: {annualized:,.2f}')
    st.write(f'ATO value: {annualized*ato_pct:,.2f}')
    st.write(f'Single WO: {annualized*single_pct:,.2f}')
    st.write(f'Two WO: {annualized*two_pct:,.2f}')
    st.write(f'Three WO: {annualized*three_pct:,.2f}')

    st.divider()
    st.subheader('Guidelines & Circulars')
    try:
        help_std = params_df.loc[params_df['Parameter']=='Is Standard Template','Help'].values[0]
    except Exception:
        help_std = ''
    if help_std:
        st.info(f'Is Standard Template — {help_std}')
    title_std, link_std = circular_for('Is Standard Template')
    if link_std:
        st.markdown(f'Circular: [{title_std}]({link_std})')
    try:
        help_ra = params_df.loc[params_df['Parameter']=='Reverse Auction','Help'].values[0]
    except Exception:
        help_ra = ''
    if help_ra:
        st.info(f'Reverse Auction — {help_ra}')
    title_ra, link_ra = circular_for('Reverse Auction')
    if link_ra:
        st.markdown(f'Circular: [{title_ra}]({link_ra})')

elif mode=='Admin':
    st.subheader('Manage Circulars & Lists')
    st.markdown('You can edit rows directly in the table. To delete rows, select them below and click "Delete selected". A backup of the existing CSV will be saved before changes are written.')

    # Editable tables
    circ_edit = st.data_editor(circ_df, num_rows='dynamic', key='circ_editor')
    lists_edit = st.data_editor(lists_df, num_rows='dynamic', key='lists_editor')
    params_edit = st.data_editor(params_df[['Parameter','Help']], num_rows='dynamic', key='params_editor')

    # Helper to create human-readable labels for each row for deletion selection
    def row_labels(df, cols):
        labels = []
        for i, row in df.reset_index(drop=True).iterrows():
            parts = [str(row.get(c, '')) for c in cols]
            labels.append(f"{i}: {' | '.join(parts)}")
        return labels

    st.markdown('---')
    st.subheader('Delete rows (safe)')

    circ_labels = row_labels(circ_edit, ['Parameter','Circular Title'])
    circ_to_delete = st.multiselect('Select circular rows to delete', circ_labels, key='circ_del')

    lists_labels = row_labels(lists_edit, ['ListName','Value'])
    lists_to_delete = st.multiselect('Select list rows to delete', lists_labels, key='lists_del')

    params_labels = row_labels(params_edit, ['Parameter','Help'])
    params_to_delete = st.multiselect('Select parameter rows to delete', params_labels, key='params_del')

    if st.button('Delete selected'):
        total = len(circ_to_delete) + len(lists_to_delete) + len(params_to_delete)
        if total == 0:
            st.warning('No rows selected for deletion.')
        else:
            st.warning(f'You are about to delete {total} row(s). This will create backups of the current CSVs.')
            if st.button('Confirm delete (this will create backup)', key='confirm_delete'):
                # Backup originals
                b1 = backup_file(CIRC_PATH)
                b2 = backup_file(LISTS_PATH)
                b3 = backup_file(PARAMS_PATH)
                backups = [p for p in [b1, b2, b3] if p]

                # Perform deletions on the edited DataFrames
                def drop_by_labels(df, labels):
                    if not labels:
                        return df
                    idxs = []
                    for lbl in labels:
                        try:
                            idx_str = lbl.split(':',1)[0]
                            idxs.append(int(idx_str))
                        except Exception:
                            continue
                    df2 = df.reset_index(drop=True)
                    # Remove any indexes that are out of range
                    idxs = [i for i in idxs if 0 <= i < len(df2)]
                    df2 = df2.drop(index=idxs)
                    return df2.reset_index(drop=True)

                circ_new = drop_by_labels(circ_edit, circ_to_delete)
                lists_new = drop_by_labels(lists_edit, lists_to_delete)
                params_new = drop_by_labels(params_edit, params_to_delete)

                # Save updated files
                try:
                    circ_new.to_csv(CIRC_PATH, index=False)
                    lists_new.to_csv(LISTS_PATH, index=False)
                    # For params, merge back with original Value column if present
                    merged = params_df.copy()
                    if 'Help' in merged.columns:
                        merged = merged.drop(columns=['Help'])
                    merged = merged.merge(params_new, on='Parameter', how='left')
                    merged.to_csv(PARAMS_PATH, index=False)
                    backups_msg = ', '.join(backups) if backups else 'none'
                    st.success(f'Deleted {total} rows. Backups created: {backups_msg}')
                except Exception as e:
                    st.error(f'Failed to save after deletion: {e}')

    if st.button('Save changes'):
        # Ensure cfg dir and move stray CSVs first
        ensure_config_and_move()
        # Backup current files
        b1 = backup_file(CIRC_PATH)
        b2 = backup_file(LISTS_PATH)
        b3 = backup_file(PARAMS_PATH)
        backups = [p for p in [b1, b2, b3] if p]
        try:
            circ_edit.to_csv(CIRC_PATH, index=False)
            lists_edit.to_csv(LISTS_PATH, index=False)
            merged = params_df.copy()
            if 'Help' in merged.columns:
                merged = merged.drop(columns=['Help'])
            merged = merged.merge(params_edit, on='Parameter', how='left')
            merged.to_csv(PARAMS_PATH, index=False)
            backups_msg = ', '.join(backups) if backups else 'none'
            st.success(f'Saved! Backups: {backups_msg}')
        except Exception as e:
            st.error(f'Failed to save changes: {e}')
