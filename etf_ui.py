# run with : streamlit run etf_ui.py
import streamlit as st
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Fund Investment Simulator", layout="wide")

st.title("📈 Fund Investment Simulator (default JEPQ : Mon 15 Sep 2025)")
st.caption("*ใช้ปันผลจากเดือนก่อนหน้าทบต้นในการ DCA เดือนถัดไป")
st.caption("*ปันผลสุทธิหักภาษี ณ ที่จ่ายอัตรา : 15%")
st.caption("*อัตราแลกเปลี่ยนจริง : THB -> USD = (อัตราแลกเปลี่ยน) + 0.1, USD -> THB = (อัตราแลกเปลี่ยน) - 0.5")
st.caption("*ค่าธรรมเนียมซื้อ/ขาย(Commission) อัตรา : 0.15% ต่อมูลค่าหลักทรัพย์ที่ซื้อขาย")
st.caption("*VAT อัตรา : 7% ของ Commission")
st.caption("*Commission และ VAT ถูกคำนวณเมื่อแปลงจาก THB -> USD แล้ว (คิดในหน่วย USD)")

# รับค่าจากผู้ใช้
initial_invest_thb = Decimal(st.number_input("💰 เงินต้นเริ่มต้น (THB)", min_value=0, value=4500))
months = st.slider("📅 ระยะเวลาลงทุน (เดือน)", 1, 240, 12)
dca_price = Decimal(st.number_input("💵 เงิน DCA (บาท/เดือน)", min_value=0, value=2000))

exchange_rate = Decimal(st.number_input("💱 อัตราแลกเปลี่ยน (USD → THB)", min_value=0.0, value=31.74, format="%.2f"))
price_per_unit_usd = Decimal(st.number_input("🏷️ ราคาต่อหน่วยกองทุน (USD)", min_value=0.0, value=56.82, format="%.2f"))
dividend_per_unit_usd = Decimal(st.number_input("💵 ปันผลต่อหน่วย (USD)", min_value=0.0, value=0.44, format="%.2f"))
withholding_tax = Decimal('0.15')  # ภาษี ณ ที่จ่าย 15%
net_dividend_rate = Decimal('1') - withholding_tax

records = []
units_held = Decimal('0')
total_invested_thb = Decimal('0')
dividend_thb_carryover = Decimal('0')
exchange_rate_buy = exchange_rate + Decimal('0.1')  # THB -> USD
exchange_rate_sell = exchange_rate - Decimal('0.5') # USD -> THB

for month in range(1, months + 1):
    if month == 1:
        invest_thb = initial_invest_thb
    else:
        invest_thb = dca_price + dividend_thb_carryover

    total_invested_thb += invest_thb

    # แปลงเป็น USD ก่อนหักค่าคอม
    invest_usd_before_fee = (invest_thb / exchange_rate_buy).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # ค่าคอม 0.15% + VAT 7% จากยอด USD
    commission_fee_usd = (invest_usd_before_fee * Decimal('0.0015')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    vat_fee_usd = (commission_fee_usd * Decimal('0.07')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    total_fee_usd = commission_fee_usd + vat_fee_usd

    # ยอด USD หลังหักค่าคอมและ VAT
    invest_usd = invest_usd_before_fee - total_fee_usd

    units_bought = (invest_usd / price_per_unit_usd).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP)
    units_held += units_bought

    gross_dividend_usd = (units_held * dividend_per_unit_usd).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    net_dividend_usd = (gross_dividend_usd * net_dividend_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    net_dividend_thb = (net_dividend_usd * exchange_rate_sell).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    dividend_thb_carryover = net_dividend_thb

    records.append({
        "เดือน": month,
        "เงินลงทุน (THB)": float(invest_thb),
        "ลงทุนสะสม (THB)": float(total_invested_thb),
        "ซื้อได้ (USD)": float(invest_usd),
        "หน่วยซื้อได้": float(units_bought),
        "หน่วยสะสม": float(units_held),
        "ปันผลก่อนหัก (USD)": float(gross_dividend_usd),
        "ปันผลหลังหัก (USD)": float(net_dividend_usd),
        "ปันผลหลังหัก (THB)": float(net_dividend_thb),
    })

df = pd.DataFrame(records)
df.set_index("เดือน", inplace=True)
st.subheader("📊 ผลลัพธ์รายเดือน")
st.dataframe(df.style.format({
    "เงินลงทุน (THB)": "฿{:,.2f}",
    "ลงทุนสะสม (THB)": "฿{:,.2f}",
    "ซื้อได้ (USD)": "${:,.2f}",
    "หน่วยซื้อได้": "{:,.6f}",
    "หน่วยสะสม": "{:,.6f}",
    "ปันผลก่อนหัก (USD)": "${:,.2f}",
    "ปันผลหลังหัก (USD)": "${:,.2f}",
    "ปันผลหลังหัก (THB)": "฿{:,.2f}"
}))

final_month = records[-1]
total_units = Decimal(final_month["หน่วยสะสม"])
total_gross_dividend_usd = sum(Decimal(m["ปันผลก่อนหัก (USD)"]) for m in records)
total_gross_dividend_thb = (total_gross_dividend_usd * exchange_rate_sell).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
total_net_dividend_usd = sum(Decimal(m["ปันผลหลังหัก (USD)"]) for m in records)
total_net_dividend_thb = sum(Decimal(m["ปันผลหลังหัก (THB)"]) for m in records)

st.subheader("📌 สรุปผลรวม")
col1, col2 = st.columns(2)
with col1:
    st.metric("💸 เงินต้นรวมที่ลงทุน", f"{total_invested_thb:,.2f} บาท")
    st.metric("📈 หน่วยกองทุนสะสม", f"{total_units:.6f} หน่วย")
with col2:
    st.metric("💰 ปันผลรวมก่อนภาษี (USD/THB)", f"{total_gross_dividend_usd:.2f} / {total_gross_dividend_thb:,.2f}")
    st.metric("🧾 ปันผลสุทธิ (USD/THB)", f"{total_net_dividend_usd:.2f} / {total_net_dividend_thb:,.2f}")

# กราฟ
df["ปันผลสะสม (THB)"] = df["ปันผลหลังหัก (THB)"].cumsum()

# --- เพิ่มคอลัมน์ใหม่: เงินต้นสะสม + ปันผลสะสม ---
df["เงินต้น+ปันผลสะสม (THB)"] = df["ลงทุนสะสม (THB)"] + df["ปันผลสะสม (THB)"]

max_invest = df["ลงทุนสะสม (THB)"].max()
max_dividend = df["ปันผลสะสม (THB)"].max()

# --- หาจุดสูงสุดของเงินต้น+ปันผลสะสม ---
max_total = df["เงินต้น+ปันผลสะสม (THB)"].max()

max_invest_month = df["ลงทุนสะสม (THB)"].idxmax()
max_dividend_month = df["ปันผลสะสม (THB)"].idxmax()

# --- จุดสูงสุดของเงินต้น+ปันผลสะสม ---
max_total_month = df["เงินต้น+ปันผลสะสม (THB)"].idxmax()

st.subheader("📉 กราฟเปรียบเทียบเงินต้นสะสม vs ปันผลสะสม vs รวม (พร้อมจุดสูงสุด)")
fig, ax = plt.subplots(figsize=(10, 5))

ax.plot(df.index, df["เงินต้น+ปันผลสะสม (THB)"], label="Accumulated Principal + Return", color='red')
ax.plot(df.index, df["ลงทุนสะสม (THB)"], label="Accumulated Investment", color='green')
ax.plot(df.index, df["ปันผลสะสม (THB)"], label="Accumulated Return", color='blue')

ax.plot(max_invest_month, max_invest, 'go')
ax.text(max_invest_month, max_invest, f"{max_invest:,.0f} ฿", color='green', fontsize=9, ha='right')

ax.plot(max_dividend_month, max_dividend, 'bo')
ax.text(max_dividend_month, max_dividend, f"{max_dividend:,.0f} ฿", color='blue', fontsize=9, ha='left')

percent_increase = (max_total - max_invest) / max_invest * 100

ax.plot(max_total_month, max_total, 'ro')
ax.text(
    max_total_month, max_total,
    f"{max_total:,.0f} ฿\n(+{percent_increase:.2f}%)",
    color='red',
    fontsize=9,
    ha='center'
)

ax.set_xlabel("Month")
ax.set_ylabel("Amount (THB)")
ax.set_title("Accumulated Principal vs Accumulated Return (THB)")
ax.legend()
ax.grid(True)

plt.tight_layout()
st.pyplot(fig)

