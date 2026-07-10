Here is a clean, comprehensive `README.md` file tailored specifically for your project. It includes setup instructions, the exact pipeline features you built, and clear documentation on how you resolved the PDF extraction hurdles.

---

# 🏦 HDFC Bank Statement Data Pipeline & Analyzer

An interactive, production-ready **Streamlit** dashboard designed to extract, sanitize, and reconstruct transaction records from unstructured HDFC Bank statement PDFs.

This application completely addresses classic PDF text-extraction traps—such as multi-line narrative fragmentation, multi-row cell concatenation, and omitted transaction rows—by implementing an intelligent chronological look-ahead math engine and regular-expression filters.

---

## ✨ Features

* **Browser-Based File Upload:** Process your local HDFC statement files completely in-memory using `pdfplumber` without local directory restrictions.
* **Timeline Alignment Engine:** A reverse-chronological pointer loop that calculates sequential state-transition balances ($\Delta$) to cleanly align withdrawals and deposits even if rows are dropped.
* **Dynamic Junk Slicing:** Automatically screens out footer lines, summary balances, and bank metadata using structural date regex validation.
* **Narration Stitching & Tokenizing:** Merges fragmented text rows (e.g., combining broken payment labels) and strips out cluttered payment gateway codes like merchant `PAYTMQR` strings.
* **Financial Ledger View:** Generates a polished DataFrame with customized font coloring (**red** for withdrawals, **green** for deposits, **blue** for running balances) formatted strictly to two decimal places.

---

## 🚀 Getting Started

### 1. Prerequisites

Make sure you have Python installed on your system. You will need to install the following dependencies:

```bash
pip install streamlit pdfplumber pandas

```

### 2. File Structure

Keep your main application file in your designated project workspace:

```text
hdfc-analyzer/
├── app.py          # The complete Streamlit source code
└── README.md       # Project documentation

```

### 3. Launching the App

Run the application locally from your terminal panel:

```bash
streamlit run app.py

```

Once executed, open your local browser to the hosted web address (typically `http://localhost:8501`).

---

## 🛠️ How It Works (The Pipeline Anatomy)

The data processor handles bank statements through four specific layers:

```text
[ Upload PDF ] ➡️ [ Regex Trim Layer ] ➡️ [ Look-Ahead Math Loop ] ➡️ [ UPI Text Sanitizer ] ➡️ [ Styled UI Table ]

```

1. **The Row Filter:** Uses `re.match(r'^\d{2}/\d{2}/\d{2}', ...)` to ensure that lines containing closing notes or secondary descriptions are safely filtered out before hitting the math grid.
2. **The Look-Ahead Strategy:** The matching sequence reads rows in reverse chronological order. If `pdfplumber` skips an unlisted system transaction fee row, the array slices (`dp[:dp_idx+1]`) act as a defense boundary, snapping pointers forward to ensure subsequent lines are not knocked out of sequence alignment.
3. **The Simple Split Tokenizer:** Looks for `"UPI-"` anchors, isolates the text block before the `@` routing symbol, and splits out long tracking hashes to instantly connect usernames to their matching transaction notes in a clear `: ` key format.

---

## 🎨 Interface Preview

* **Summary Cards:** Instantly view **Total Debits (Withdrawals)**, **Total Credits (Deposits)**, and total active transaction row counts before diving into the main sheet.
* **Interactive Table:** Filter, search, and track rows using a ledger view starting cleanly at index `1`.

---

Congratulations on locking down this backend project and taking it to production! 🚀