import streamlit as st
import pdfplumber
import pandas as pd
import re

# Set up clean Streamlit layout configuration
st.set_page_config(page_title="HDFC Statement Analyzer", layout="wide")
st.title("🏦 HDFC Bank Statement Data Pipeline")
st.write("Upload your bank statement PDF to extract, sequence, and sanitize transaction records.")

def get_proper_lean(wd, dp, bal):
    wd_seq = [-1] * len(bal)
    dp_seq = [-1] * len(bal)
    wd_idx, dp_idx = len(wd) - 1, len(dp) - 1

    for bal_idx in range(len(bal) - 1, 0, -1):
        diff = round(bal[bal_idx] - bal[bal_idx - 1], 2)

        if diff > 0:  # Deposit
            if diff in dp[:dp_idx + 1]:
                match_idx = len(dp[:dp_idx + 1]) - 1 - dp[:dp_idx + 1][::-1].index(diff)
                dp_idx = match_idx
                dp_seq[bal_idx] = dp[dp_idx]
                dp_idx -= 1
            else:
                dp_seq[bal_idx] = diff  # Fallback to math

        elif diff < 0:  # Withdrawal
            abs_diff = abs(diff)
            if abs_diff in wd[:wd_idx + 1]:
                match_idx = len(wd[:wd_idx + 1]) - 1 - wd[:wd_idx + 1][::-1].index(abs_diff)
                wd_idx = match_idx
                wd_seq[bal_idx] = wd[wd_idx]
                wd_idx -= 1
            else:
                wd_seq[bal_idx] = abs_diff  # Fallback to math

    # Boundary handling for Index 0
    if wd_idx >= 0: wd_seq[0] = wd[0]
    elif dp_idx >= 0: dp_seq[0] = dp[0]
            
    return wd_seq, dp_seq


def to_list(raw_table):
    dates = []
    narrations = []
    withdrawals = []
    deposits = []
    balances = []

    for i, row in enumerate(raw_table):
        date_cell = row[0]
        narration_cell = row[1]
        withdrawal_cell = row[4]
        deposit_cell = row[5]
        balance_cell = row[6]

        dates.extend(date_cell.strip().split('\n') if date_cell else "")
        narrations.append(narration_cell.strip() if narration_cell else "")

        if withdrawal_cell is None:
            withdrawals.append(0.0)
        else:
            wd_items = [float(amt.strip().replace(',', '')) for amt in withdrawal_cell.split('\n') if amt.strip()]
            withdrawals.extend(wd_items if wd_items else [0.0])

        if deposit_cell is None:
            deposits.append(0.0)
        else:
            dp_items = [float(amt.strip().replace(',', '')) for amt in deposit_cell.split('\n') if amt.strip()]
            deposits.extend(dp_items if dp_items else [0.0])

        if balance_cell is None:
            balances.append(0.0)
        else:
            bal_items = [float(amt.strip().replace(',', '')) for amt in balance_cell.split('\n') if amt.strip()]
            balances.extend(bal_items if bal_items else [0.0])
            
    return dates, narrations, withdrawals, deposits, balances


def normalize_and_split_narrations(all_titles):
    raw_text_stream = "\n".join(all_titles)
    prefixes = r'(?:UPI-|DEBIT CARD|IMPS-|NEFT-|NWD-|CHQ DEPOSIT|MANAGEMENT FEE|INTEREST|HAB)'
    split_pattern = re.compile(rf'\n(?={prefixes})')
    raw_segments = split_pattern.split(raw_text_stream)
    
    final_clean_narrations = []
    for segment in raw_segments:
        segment_text = segment.strip()
        if segment_text:
            cleaned_segment = segment_text.replace('\n', ' ')
            cleaned_segment = re.sub(r'\s+', ' ', cleaned_segment)
            final_clean_narrations.append(cleaned_segment)
            
    return final_clean_narrations


def clean_upi_with_split(clean_narrations):
    parsed_narrations = []
    
    for text in clean_narrations:
        text = text.strip()
        
        if text.startswith("UPI-"):
            username_part = text.split('@', 1)[0]
            username = username_part.split('-')[1].strip()
            message = text.rsplit('-', 1)[-1].strip()
            parsed_narrations.append(f"{username}: {message}")
        else:
            parsed_narrations.append(text)
            
    return parsed_narrations


# --- UPDATED TEXT COLOR STYLING FUNCTION ---
def highlight_cols(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)
    
    # Text color red for active withdrawals
    styles["Withdrawal (Dr)"] = df["Withdrawal (Dr)"].apply(
        lambda v: "color: #cc0000; font-weight: bold;" if v != "-" else ""
    )
    # Text color green for active deposits
    styles["Deposit (Cr)"] = df["Deposit (Cr)"].apply(
        lambda v: "color: #008800; font-weight: bold;" if v != "-" else ""
    )
    # Text color light blue for running balances
    styles["Running Balance"] = "color: #3399ff; font-weight: bold;"
    
    return styles


# --- STREAMLIT USER INTERFACE FILE UPLOADER ---
uploaded_file = st.file_uploader("Choose an HDFC Bank Statement PDF", type=["pdf"])

if uploaded_file is not None:
    all_dates = []
    all_titles = []
    all_withdrawals = []
    all_deposits = []
    all_balances = []

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            raw_table = page.extract_table()

            if raw_table:
                if len(raw_table) == 2:
                    data_rows = raw_table[1:]
                else:
                    data_rows = raw_table

                trimmed_table = []
                for row in data_rows:
                    date_cell = row[0] if row[0] else ""
                    if re.match(r'^\d{2}/\d{2}/\d{2}', str(date_cell).strip()):
                        trimmed_table.append(row)

                if trimmed_table:
                    dates, narrations, withdrawals, deposits, balances = to_list(trimmed_table)
                    all_dates.extend(dates)
                    all_titles.extend(narrations)
                    all_withdrawals.extend(withdrawals)
                    all_deposits.extend(deposits)
                    all_balances.extend(balances)

    withdrawal_sequence, deposit_sequence = get_proper_lean(all_withdrawals, all_deposits, all_balances)
    finalized_texts = normalize_and_split_narrations(all_titles)
    parsed_narrations = clean_upi_with_split(finalized_texts)

    min_length = min(len(all_dates), len(parsed_narrations), len(all_balances))
    
    df_data = {
        "Date": all_dates[:min_length],
        "Narration / Description": parsed_narrations[:min_length],
        "Withdrawal (Dr)": [f"{w:.2f}" if w > 0 else "-" for w in withdrawal_sequence[:min_length]],
        "Deposit (Cr)": [f"{d:.2f}" if d > 0 else "-" for d in deposit_sequence[:min_length]],
        "Running Balance": [f"{b:.2f}" for b in all_balances[:min_length]]
    }
    
    df = pd.DataFrame(df_data)
    df.index = df.index + 1

    total_withdrawn = sum([w for w in withdrawal_sequence if w > 0])
    total_deposited = sum([d for d in deposit_sequence if d > 0])

    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Total Debits (Withdrawals)", f"₹{total_withdrawn:,.2f}")
    with m2:
        st.metric("Total Credits (Deposits)", f"₹{total_deposited:,.2f}")
    with m3:
        st.metric("Total Extracted Transactions", len(df))

    st.markdown("---")
    st.subheader("📋 Parsed Transaction Ledger Table")
    
    # Apply the styling wrapper to the dataframe view
    styled_df = df.style.apply(highlight_cols, axis=None)
    
    st.dataframe(styled_df, use_container_width=True)